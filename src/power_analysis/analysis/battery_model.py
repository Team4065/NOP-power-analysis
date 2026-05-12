"""Model battery internal resistance from voltage sag during current draws.

Physical model:
    V_terminal = V_oc - I * R_internal

Where:
    V_terminal  = measured battery terminal voltage (from telemetry)
    V_oc        = open-circuit voltage (battery at rest, no load)
    I           = current draw (from telemetry)
    R_internal  = internal resistance we are estimating (Ohms)

A new battery typically has R_internal ≈ 0.010–0.015 Ω.
A worn battery may reach 0.030+ Ω.
"""

from __future__ import annotations

import numpy as np  # noqa: F401
import pandas as pd

from power_analysis import config  # noqa: F401


class BatteryModel:
    """Estimate battery internal resistance from telemetry.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry data as returned by ``TelemetryParser.load()``.

    Example
    -------
    >>> model = BatteryModel(df)
    >>> r = model.estimate_internal_resistance()
    >>> print(f"R_internal = {r:.4f} Ω")
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def estimate_internal_resistance(self) -> float:
        """Estimate battery internal resistance in Ohms using linear regression.

        Returns
        -------
        float
            Estimated R_internal (Ω).

        Hint
        ----
        1. Filter to enabled rows (avoids resting-voltage contamination).
        2. Use np.polyfit(current_values, voltage_values, deg=1).
           polyfit returns [slope, intercept].
           From V = V_oc - I * R, the slope equals -R_internal.
        3. Return the absolute value of the slope.
        """
        # TODO: Filter self.df to rows where config.ENABLED_COL is True
        # TODO: Extract current (x) and voltage (y) arrays
        # TODO: Fit with np.polyfit(x, y, deg=1) — slope is at index [0]
        # TODO: Return abs(slope) as R_internal
        raise NotImplementedError("Implement BatteryModel.estimate_internal_resistance()")

    def open_circuit_voltage(self) -> float:
        """Estimate the open-circuit voltage (V_oc) from the regression intercept.

        Returns
        -------
        float
            Estimated V_oc (V).

        Hint: The intercept from the same np.polyfit call gives V_oc.
        """
        # TODO: Reuse the polyfit logic from estimate_internal_resistance
        # TODO: Return the intercept (index [1] of the polyfit result)
        raise NotImplementedError("Implement BatteryModel.open_circuit_voltage()")
