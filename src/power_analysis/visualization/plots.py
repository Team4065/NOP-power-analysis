"""Matplotlib plotting functions for AKit match power data.

All plots operate on the normalized DataFrame produced by ``AKitParser.load()``
and an x-axis of ``elapsed_s``. Every time-series plot is annotated with up to
four vertical match-period lines (auto start, teleop start, endgame start,
match end) via :func:`add_period_lines`.

Headless safety: on Linux without a DISPLAY, the Agg backend is selected before
pyplot is imported so plots render to PNG without a windowing system.
"""

from __future__ import annotations

import os
import platform
from typing import NamedTuple

import matplotlib

# Select a non-interactive backend on headless Linux before importing pyplot.
if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
    matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from power_analysis import config  # noqa: E402

# Colors / styles for the four match-period boundary lines
_PERIOD_STYLE = {
    "match_start": ("tab:green", "Match start"),
    "teleop_start": ("tab:blue", "Teleop start"),
    "endgame_start": ("tab:orange", "Endgame start"),
    "match_end": ("tab:red", "Match end"),
}


class MatchPeriods(NamedTuple):
    """Elapsed-time boundaries (seconds) of each match period.

    Boundaries that do not occur within the data are ``None`` (e.g. a
    capture that ends during autonomous has no teleop_start).
    """

    match_start: float
    teleop_start: float | None
    endgame_start: float | None
    match_end: float


def match_periods(df: pd.DataFrame) -> MatchPeriods:
    """Compute match-period boundaries from a normalized AKit DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized match DataFrame (must contain elapsed_s, autonomous,
        and match_time_remaining columns).

    Returns
    -------
    MatchPeriods
    """
    elapsed = df[config.ELAPSED_COL]
    autonomous = df[config.AUTONOMOUS_OUT_COL]

    match_start = float(elapsed.iloc[0])
    match_end = float(elapsed.iloc[-1])

    # Teleop begins at the first non-autonomous row.
    teleop_rows = df[~autonomous]
    teleop_start = (
        float(teleop_rows[config.ELAPSED_COL].iloc[0]) if not teleop_rows.empty else None
    )

    # Endgame begins at the first teleop row with MatchTime <= ENDGAME_SECONDS.
    endgame_start = None
    if not teleop_rows.empty:
        endgame_rows = teleop_rows[
            teleop_rows[config.MATCH_TIME_REMAINING_COL] <= config.ENDGAME_SECONDS
        ]
        if not endgame_rows.empty:
            endgame_start = float(endgame_rows[config.ELAPSED_COL].iloc[0])

    return MatchPeriods(
        match_start=match_start,
        teleop_start=teleop_start,
        endgame_start=endgame_start,
        match_end=match_end,
    )


def add_period_lines(ax: plt.Axes, periods: MatchPeriods) -> None:
    """Draw labeled vertical lines for each match-period boundary on ``ax``.

    Boundaries that are ``None`` (did not occur within the data) are skipped.
    """
    for field_name in periods._fields:
        value = getattr(periods, field_name)
        if value is None:
            continue
        color, label = _PERIOD_STYLE[field_name]
        ax.axvline(
            value,
            color=color,
            linestyle="--",
            linewidth=1.2,
            alpha=0.8,
            label=label,
        )


# ---------------------------------------------------------------------------
# Time-series plots
# ---------------------------------------------------------------------------

def plot_voltage(df: pd.DataFrame, session_label: str = "") -> plt.Figure:
    """Plot 12V battery voltage over elapsed match time.

    Adds a horizontal brownout-threshold line, shades any browned-out regions,
    and draws the four match-period vertical lines.
    """
    fig, ax = plt.subplots(figsize=(11, 5))
    elapsed = df[config.ELAPSED_COL]
    voltage = df[config.VOLTAGE_12V_COL]

    ax.plot(elapsed, voltage, color="tab:purple", linewidth=1.0, label="Battery voltage")

    # Brownout threshold reference line
    ax.axhline(
        config.BROWNOUT_THRESHOLD,
        color="red",
        linestyle=":",
        linewidth=1.5,
        label=f"Brownout threshold ({config.BROWNOUT_THRESHOLD}V)",
    )

    # Shade browned-out regions if the signal is present
    if config.BROWNED_OUT_OUT_COL in df.columns and df[config.BROWNED_OUT_OUT_COL].any():
        ax.fill_between(
            elapsed,
            voltage.min(),
            voltage.max(),
            where=df[config.BROWNED_OUT_OUT_COL].to_numpy(),
            color="red",
            alpha=0.15,
            label="Brownout",
        )

    add_period_lines(ax, match_periods(df))

    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(_title("Battery Voltage", session_label))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


def plot_total_current(df: pd.DataFrame, session_label: str = "") -> plt.Figure:
    """Plot total battery current draw over elapsed match time."""
    fig, ax = plt.subplots(figsize=(11, 5))
    elapsed = df[config.ELAPSED_COL]
    current = df[config.CURRENT_TOTAL_COL]

    ax.plot(elapsed, current, color="tab:red", linewidth=1.0, label="Total current")
    ax.fill_between(elapsed, 0, current, color="tab:red", alpha=0.15)

    add_period_lines(ax, match_periods(df))

    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Current (A)")
    ax.set_title(_title("Total Battery Current", session_label))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


def plot_current_by_subsystem(df: pd.DataFrame, session_label: str = "") -> plt.Figure:
    """Stacked area chart of per-subsystem current draw over elapsed match time."""
    fig, ax = plt.subplots(figsize=(11, 5))
    elapsed = df[config.ELAPSED_COL]

    subsystems = list(config.AKIT_MOTOR_CURRENT_COLS)
    stack_cols = [f"current_{s}" for s in subsystems]
    present = [(s, c) for s, c in zip(subsystems, stack_cols) if c in df.columns]

    if present:
        labels = [s for s, _ in present]
        # Clamp tiny negative idle-sensor readings to 0 so the stack reads cleanly.
        series = [df[c].clip(lower=0).to_numpy() for _, c in present]
        ax.stackplot(elapsed, *series, labels=labels, alpha=0.85)

    add_period_lines(ax, match_periods(df))

    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Current (A)")
    ax.set_title(_title("Current by Subsystem", session_label))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Summary plot
# ---------------------------------------------------------------------------

def plot_energy_rank(
    breakdown: dict[str, float], session_label: str = ""
) -> plt.Figure:
    """Horizontal bar chart of subsystem energy, ranked descending, with percent labels.

    Parameters
    ----------
    breakdown : dict[str, float]
        Mapping subsystem name → energy (Wh), e.g. from
        ``PowerModel.subsystem_energy_breakdown()``.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    ranked = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)
    names = [n for n, _ in ranked]
    values = [v for _, v in ranked]
    total = sum(values)

    # Plot top-to-bottom in descending order.
    y_pos = range(len(names))
    bars = ax.barh(list(y_pos), values, color="tab:blue", alpha=0.8)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # largest at top

    # Annotate each bar with Wh and % of total.
    for bar, value in zip(bars, values):
        pct = (100.0 * value / total) if total else 0.0
        ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f"  {value * 1000:.0f} mWh ({pct:.1f}%)",
            va="center",
            ha="left",
            fontsize=8,
        )

    ax.set_xlabel("Energy (Wh)")
    ax.set_title(_title("Energy by Subsystem (ranked)", session_label))
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title(base: str, session_label: str) -> str:
    """Compose a plot title with an optional session label suffix."""
    return f"{base} — {session_label}" if session_label else base
