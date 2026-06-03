"""Detect and characterize voltage brownout events.

FRC robots experience a brownout when battery terminal voltage drops below the
configured threshold — the roboRIO automatically disables motor outputs to
protect electronics. Team 4065 configures this threshold at 6.0 V (not the
WPILib default of 6.8 V). Brownouts are typically caused by high instantaneous
current draw exceeding the battery's ability to maintain voltage (I × R_internal).

For AKit logs, the preferred detection path uses the /SystemStats/BrownedOut
boolean signal directly (available as the normalized ``browned_out`` column).
When that column is absent (legacy data), the detector falls back to thresholding
the voltage column.
"""

from __future__ import annotations

import pandas as pd

from power_analysis import config


class BrownoutDetector:
    """Find brownout events in a normalized telemetry DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized telemetry data. Must contain a time column and either a
        ``browned_out`` boolean column (preferred) or a voltage column
        (``voltage_12v`` or ``voltage_battery``) for threshold fallback.
    threshold : float
        Voltage (V) below which a brownout is declared in fallback mode.
        Defaults to ``config.BROWNOUT_THRESHOLD`` (6.0 V for Team 4065).

    Example
    -------
    >>> detector = BrownoutDetector(df)
    >>> events = detector.detect()
    >>> print(f"{detector.brownout_count()} brownout(s) detected")
    """

    def __init__(
        self,
        df: pd.DataFrame,
        threshold: float = config.BROWNOUT_THRESHOLD,
    ) -> None:
        self.df = df
        self.threshold = threshold
        self._time_col = self._resolve_time_col(df)
        self._voltage_col = self._resolve_voltage_col(df)
        self._use_signal = config.BROWNED_OUT_OUT_COL in df.columns

    def detect(self) -> pd.DataFrame:
        """Find all brownout events and return their statistics.

        Returns
        -------
        pd.DataFrame
            One row per brownout event with columns:
            ``start_time``, ``end_time``, ``duration_s``, ``min_voltage``.
            Empty DataFrame (with those columns) if no events occurred.
        """
        below = self._brownout_mask()

        events = []
        if below.any():
            # Assign a group id to each contiguous run of equal mask values,
            # then keep only the runs where the mask is True.
            group_id = (below != below.shift()).cumsum()
            for _, group in self.df[below].groupby(group_id[below]):
                start_time = float(group[self._time_col].iloc[0])
                end_time = float(group[self._time_col].iloc[-1])
                min_voltage = (
                    float(group[self._voltage_col].min())
                    if self._voltage_col is not None
                    else float("nan")
                )
                events.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_s": end_time - start_time,
                    "min_voltage": min_voltage,
                })

        return pd.DataFrame(
            events,
            columns=["start_time", "end_time", "duration_s", "min_voltage"],
        )

    def brownout_count(self) -> int:
        """Return the total number of brownout events in the match."""
        return len(self.detect())

    def total_brownout_duration(self) -> float:
        """Return the summed duration (seconds) of all brownout events."""
        events = self.detect()
        if events.empty:
            return 0.0
        return float(events["duration_s"].sum())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _brownout_mask(self) -> pd.Series:
        """Boolean Series — True where the robot is in brownout."""
        if self._use_signal:
            return self.df[config.BROWNED_OUT_OUT_COL].astype(bool)
        if self._voltage_col is not None:
            return self.df[self._voltage_col] < self.threshold
        raise ValueError(
            "DataFrame has neither a 'browned_out' column nor a voltage column "
            "for brownout detection."
        )

    @staticmethod
    def _resolve_time_col(df: pd.DataFrame) -> str:
        """Return the name of the time column, or the index as a fallback."""
        if config.ELAPSED_COL in df.columns:
            return config.ELAPSED_COL
        if config.TIMESTAMP_COL in df.columns:
            return config.TIMESTAMP_COL
        # Legacy index-based time: expose the index as a column reference
        return df.index.name or "index"

    @staticmethod
    def _resolve_voltage_col(df: pd.DataFrame) -> str | None:
        """Return the name of the voltage column, or None if absent."""
        if config.VOLTAGE_12V_COL in df.columns:
            return config.VOLTAGE_12V_COL
        if config.VOLTAGE_COL in df.columns:
            return config.VOLTAGE_COL
        return None
