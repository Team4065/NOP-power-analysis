"""Calculate electrical power and energy from telemetry data.

Key physics:
    Power (W)  = Voltage (V) × Current (A)
    Energy (J) = ∫ Power dt   (use trapezoidal integration)
    Energy (Wh) = Energy (J) / 3600

PowerModel auto-detects its input schema:
  * AKit normalized DataFrame (from AKitParser) — uses voltage_12v, current_total,
    elapsed_s column for time, and per-subsystem current_<group> columns.
  * Legacy flat schema (from TelemetryParser) — uses voltage_battery, current_total,
    and the timestamp index for time.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd

from power_analysis import config


class VoltageStats(NamedTuple):
    """Summary of battery voltage amplitude over the match window."""

    min_v: float
    max_v: float
    mean_v: float
    drop_v: float  # max_v - min_v (amplitude of the voltage sag)


class PowerModel:
    """Compute power metrics from a telemetry DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Either an AKit normalized DataFrame (from ``AKitParser.load()``) or a
        legacy flat-schema DataFrame (from ``TelemetryParser.load()``).
        Schema is auto-detected from the columns present.

    Example
    -------
    >>> model = PowerModel(df)
    >>> watts = model.compute_instantaneous_power()
    >>> wh = model.compute_energy()
    >>> ranking = model.rank_by_energy()  # AKit mode only
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._akit = config.VOLTAGE_12V_COL in df.columns

        if self._akit:
            self._voltage_col = config.VOLTAGE_12V_COL
            self._current_col = config.CURRENT_TOTAL_COL
            self._enabled_col = config.ENABLED_OUT_COL
            self._time = df[config.ELAPSED_COL].to_numpy()
        else:
            self._voltage_col = config.VOLTAGE_COL
            self._current_col = config.CURRENT_COL
            self._enabled_col = config.ENABLED_COL
            self._time = np.asarray(df.index, dtype=float)

    # ------------------------------------------------------------------
    # Core power / energy
    # ------------------------------------------------------------------

    def compute_instantaneous_power(self) -> pd.Series:
        """Return instantaneous power in Watts at each timestep.

        Power = Voltage × Current.
        """
        return self.df[self._voltage_col] * self.df[self._current_col]

    def compute_energy(self) -> float:
        """Return total energy consumed over the match in Watt-hours.

        Uses trapezoidal integration over the time axis (elapsed_s in AKit mode,
        timestamp index in legacy mode), which correctly handles the non-uniform
        sample intervals of AdvantageKit logs.
        """
        power = self.compute_instantaneous_power().to_numpy()
        return self._integrate_to_wh(power)

    def peak_power(self) -> float:
        """Return the maximum instantaneous power draw in Watts."""
        return float(self.compute_instantaneous_power().max())

    def average_power(self) -> float:
        """Return the mean power draw over enabled periods in Watts."""
        enabled_df = self.df[self.df[self._enabled_col]]
        power = enabled_df[self._voltage_col] * enabled_df[self._current_col]
        return float(power.mean())

    # ------------------------------------------------------------------
    # Subsystem breakdown (AKit mode only)
    # ------------------------------------------------------------------

    def subsystem_energy_breakdown(self) -> dict[str, float]:
        """Return energy (Wh) consumed by each subsystem group.

        For each subsystem, energy = ∫ (voltage × subsystem_current) dt.
        Because the per-subsystem currents sum to current_total and voltage is a
        common factor, the returned values sum to ``compute_energy()``.

        Returns
        -------
        dict[str, float]
            Mapping of subsystem name → energy in Wh.

        Raises
        ------
        AttributeError
            If called on a legacy (non-AKit) DataFrame that lacks subsystem columns.
        """
        if not self._akit:
            raise AttributeError(
                "subsystem_energy_breakdown() requires an AKit DataFrame "
                "(no per-subsystem current columns found in legacy schema)."
            )

        voltage = self.df[self._voltage_col].to_numpy()
        breakdown: dict[str, float] = {}
        for subsystem in config.AKIT_MOTOR_CURRENT_COLS:
            col = f"current_{subsystem}"
            if col not in self.df.columns:
                breakdown[subsystem] = 0.0
                continue
            power = voltage * self.df[col].to_numpy()
            breakdown[subsystem] = self._integrate_to_wh(power)
        return breakdown

    def rank_by_energy(self) -> list[tuple[str, float]]:
        """Return subsystems ranked by energy consumed, descending.

        Returns
        -------
        list[tuple[str, float]]
            ``[(subsystem_name, energy_wh), ...]`` sorted highest energy first.
        """
        breakdown = self.subsystem_energy_breakdown()
        return sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)

    # ------------------------------------------------------------------
    # Voltage amplitude
    # ------------------------------------------------------------------

    def voltage_stats(self) -> VoltageStats:
        """Return min, max, mean, and drop (max-min) of battery voltage.

        Note
        ----
        ``drop_v`` is the voltage amplitude across the match window (max − min).
        Because the parser retains only the enabled match window, the maximum
        within the window approximates the pre-match idle voltage.
        """
        v = self.df[self._voltage_col]
        min_v = float(v.min())
        max_v = float(v.max())
        mean_v = float(v.mean())
        return VoltageStats(
            min_v=min_v,
            max_v=max_v,
            mean_v=mean_v,
            drop_v=max_v - min_v,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _integrate_to_wh(self, power_watts: np.ndarray) -> float:
        """Trapezoidally integrate a power array over the time axis → Wh."""
        if len(power_watts) < 2:
            return 0.0
        joules = np.trapezoid(power_watts, x=self._time)
        return float(joules / 3600.0)
