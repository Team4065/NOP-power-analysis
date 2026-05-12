"""Calculate electrical power and energy from telemetry data.

Key physics:
    Power (W)  = Voltage (V) × Current (A)
    Energy (J) = ∫ Power dt   (use trapezoidal integration)
    Energy (Wh) = Energy (J) / 3600
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from power_analysis import config


class PowerModel:
    """Compute power metrics from a telemetry DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry data as returned by ``TelemetryParser.load()``.
        Must be indexed by timestamp and contain at minimum
        ``voltage_battery`` and ``current_total`` columns.

    Example
    -------
    >>> model = PowerModel(df)
    >>> watts = model.compute_instantaneous_power()
    >>> wh = model.compute_energy()
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def compute_instantaneous_power(self) -> pd.Series:
        """Return instantaneous power in Watts at each timestep.

        Returns
        -------
        pd.Series
            Power (W) indexed by timestamp.

        Hint: Power = Voltage × Current — multiply the two columns.
        """
        return self.df[config.VOLTAGE_COL] * self.df[config.CURRENT_COL]

    def compute_energy(self) -> float:
        """Return total energy consumed over the match in Watt-hours.

        Returns
        -------
        float
            Energy in Wh.

        Hint: Use np.trapz(power_values, x=timestamps) to integrate.
        The result is in Joules; divide by 3600 to convert to Wh.
        """
        power = self.compute_instantaneous_power()
        joules = np.trapezoid(power.values, x=self.df.index)
        return joules / 3600

    def peak_power(self) -> float:
        """Return the maximum instantaneous power draw in Watts.

        Returns
        -------
        float
            Peak power (W).
        """
        return float(self.compute_instantaneous_power().max())

    def average_power(self) -> float:
        """Return the mean power draw over enabled periods in Watts.

        Returns
        -------
        float
            Mean power (W) during enabled (robot_enabled == True) rows only.

        Hint: Filter self.df to rows where config.ENABLED_COL is True before averaging.
        """
        enabled_df = self.df[self.df[config.ENABLED_COL]]
        power = enabled_df[config.VOLTAGE_COL] * enabled_df[config.CURRENT_COL]
        return float(power.mean())
