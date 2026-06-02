"""Detect and characterize voltage brownout events.

FRC robots experience a brownout when battery terminal voltage drops below the
configured threshold — the roboRIO automatically disables motor outputs to
protect electronics. Team 4065 configures this threshold at 6.0 V (not the
WPILib default of 6.8 V). Brownouts are typically caused by high instantaneous
current draw exceeding the battery's ability to maintain voltage (I × R_internal).

For AKit logs, prefer using the /SystemStats/BrownedOut boolean signal directly
(available as the normalized ``browned_out`` column) rather than applying
threshold math to battery voltage.
"""

from __future__ import annotations

import pandas as pd

from power_analysis import config


class BrownoutDetector:
    """Find brownout events in telemetry data.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry data as returned by ``TelemetryParser.load()``.
    threshold : float
        Voltage (V) below which a brownout is declared.
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

    def detect(self) -> pd.DataFrame:
        """Find all brownout events and return their statistics.

        Returns
        -------
        pd.DataFrame
            One row per brownout event with columns:
            ``start_time``, ``end_time``, ``duration_s``, ``min_voltage``.

        Hint
        ----
        1. Create a boolean Series: ``below = df[VOLTAGE_COL] < self.threshold``.
        2. Use ``(below != below.shift()).cumsum()`` to assign a group ID to each
           contiguous block of rows.
        3. Keep only groups where ``below`` is True.
        4. For each surviving group, record:
           - start_time  = first timestamp index value in the group
           - end_time    = last timestamp index value in the group
           - duration_s  = end_time - start_time
           - min_voltage = minimum voltage in the group
        """
        # TODO: Build the boolean mask for below-threshold voltage
        # TODO: Label contiguous regions with a group ID
        # TODO: Iterate (or groupby) over brownout regions
        # TODO: Collect stats into a list of dicts and return as a DataFrame
        raise NotImplementedError("Implement BrownoutDetector.detect()")

    def brownout_count(self) -> int:
        """Return the total number of brownout events in the match.

        Returns
        -------
        int
        """
        # TODO: Call self.detect() and return the number of rows
        raise NotImplementedError("Implement BrownoutDetector.brownout_count()")
