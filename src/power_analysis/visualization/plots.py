"""Reusable plotting functions for telemetry and power data.

All functions return a Matplotlib Figure so they can be embedded in either
the Streamlit dashboard or a Jupyter notebook.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from power_analysis import config  # noqa: F401


def plot_voltage(df: pd.DataFrame) -> plt.Figure:
    """Plot battery voltage over match time.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry DataFrame indexed by timestamp.

    Returns
    -------
    matplotlib.figure.Figure
    """
    # TODO: Create a Figure and Axes with plt.subplots()
    # TODO: Plot df[config.VOLTAGE_COL] vs the timestamp index
    # TODO: Add a horizontal dashed red line at config.BROWNOUT_THRESHOLD
    # TODO: Label axes and add a title
    # TODO: Return the Figure
    raise NotImplementedError("Implement plot_voltage()")


def plot_current(df: pd.DataFrame) -> plt.Figure:
    """Plot total current draw over match time.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry DataFrame indexed by timestamp.

    Returns
    -------
    matplotlib.figure.Figure
    """
    # TODO: Plot df[config.CURRENT_COL] vs timestamp
    # TODO: Label axes and add a title
    # TODO: Return the Figure
    raise NotImplementedError("Implement plot_current()")


def plot_power(df: pd.DataFrame, power: pd.Series) -> plt.Figure:
    """Plot instantaneous power over match time.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry DataFrame (used for timestamp index).
    power : pd.Series
        Power values (W) as returned by ``PowerModel.compute_instantaneous_power()``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    # TODO: Plot power vs timestamp index
    # TODO: Shade the area under the curve with ax.fill_between for visual impact
    # TODO: Label axes and add a title
    # TODO: Return the Figure
    raise NotImplementedError("Implement plot_power()")


def plot_channel_breakdown(df: pd.DataFrame) -> plt.Figure:
    """Stacked area chart showing per-PDH-channel current draw over time.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry DataFrame indexed by timestamp.

    Returns
    -------
    matplotlib.figure.Figure
    """
    # TODO: Use ax.stackplot with df[config.PDH_CHANNEL_COLS].T values
    # TODO: Add a legend mapping channel numbers to subsystem names (see telemetry_schema.md)
    # TODO: Return the Figure
    raise NotImplementedError("Implement plot_channel_breakdown()")
