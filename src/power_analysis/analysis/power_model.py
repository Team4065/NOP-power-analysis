"""Calculate electrical power and energy from telemetry data.

Key physics:
    Power (W)  = Voltage (V) × Current (A)
    Energy (J) = ∫ Power dt   (use trapezoidal integration)
    Energy (Wh) = Energy (J) / 3600
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd

from power_analysis import config  # noqa: F401


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
        # TODO: Multiply config.VOLTAGE_COL by config.CURRENT_COL
        # TODO: Return the result as a pd.Series with the same index as self.df
        raise NotImplementedError("Implement PowerModel.compute_instantaneous_power()")

    def compute_energy(self) -> float:
        """Return total energy consumed over the match in Watt-hours.

        Returns
        -------
        float
            Energy in Wh.

        Hint: Use np.trapz(power_values, x=timestamps) to integrate.
        The result is in Joules; divide by 3600 to convert to Wh.
        """
        # TODO: Call self.compute_instantaneous_power() to get power values
        # TODO: Get the timestamp index (self.df.index) as the x-axis
        # TODO: Integrate with np.trapz
        # TODO: Convert from Joules to Watt-hours and return
        raise NotImplementedError("Implement PowerModel.compute_energy()")

    def peak_power(self) -> float:
        """Return the maximum instantaneous power draw in Watts.

        Returns
        -------
        float
            Peak power (W).
        """
        # TODO: Use compute_instantaneous_power() then find the max
        raise NotImplementedError("Implement PowerModel.peak_power()")

    def average_power(self) -> float:
        """Return the mean power draw over enabled periods in Watts.

        Returns
        -------
        float
            Mean power (W) during enabled (robot_enabled == True) rows only.

        Hint: Filter self.df to rows where config.ENABLED_COL is True before averaging.
        """
        # TODO: Filter to enabled rows
        # TODO: Compute power on the filtered DataFrame
        # TODO: Return the mean
        raise NotImplementedError("Implement PowerModel.average_power()")
