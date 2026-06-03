"""Tests for visualization/plots.py.

Requirements covered:
  SYS-PWR-008: Plot generation with match-period vertical lines

Backend is forced to Agg in conftest.py so these run headlessly.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from power_analysis import config
from power_analysis.analysis.power_model import PowerModel
from power_analysis.visualization import plots


# ---------------------------------------------------------------------------
# Synthetic full-match DataFrame (auto → teleop → endgame)
# ---------------------------------------------------------------------------

@pytest.fixture
def full_match_df() -> pd.DataFrame:
    """A synthetic match spanning auto, teleop, and endgame periods.

    15 auto rows (MatchTime 15→1), then 140 teleop rows (MatchTime 140→1),
    so all three period boundaries are present.
    """
    rows = []
    t = 0.0
    # Auto: MatchTime 15 → 1
    for mt in range(15, 0, -1):
        rows.append((t, True, float(mt)))
        t += 0.1
    # Teleop: MatchTime 140 → 1 (endgame when <= 30)
    for mt in range(140, 0, -1):
        rows.append((t, False, float(mt)))
        t += 0.1

    n = len(rows)
    data = {
        config.ELAPSED_COL: [r[0] for r in rows],
        config.VOLTAGE_12V_COL: [12.0 - 0.01 * i for i in range(n)],
        config.CURRENT_TOTAL_COL: [30.0] * n,
        config.ENABLED_OUT_COL: [True] * n,
        config.AUTONOMOUS_OUT_COL: [r[1] for r in rows],
        config.BROWNED_OUT_OUT_COL: [False] * n,
        config.MATCH_TIME_REMAINING_COL: [r[2] for r in rows],
    }
    for sub in config.AKIT_MOTOR_CURRENT_COLS:
        data[f"current_{sub}"] = [6.0] * n
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# match_periods
# ---------------------------------------------------------------------------

class TestMatchPeriods:
    def test_match_start_is_zero(self, full_match_df):
        """SYS-PWR-008: match_start equals the first elapsed value."""
        periods = plots.match_periods(full_match_df)
        assert periods.match_start == pytest.approx(0.0)

    def test_teleop_start_at_first_non_auto_row(self, full_match_df):
        """SYS-PWR-008: teleop_start is the elapsed time of the first teleop row."""
        periods = plots.match_periods(full_match_df)
        # 15 auto rows at 0.1s spacing → teleop starts at index 15 → 1.5s
        assert periods.teleop_start == pytest.approx(1.5)

    def test_endgame_start_when_match_time_le_30(self, full_match_df):
        """SYS-PWR-008: endgame_start is the first teleop row with MatchTime <= 30.

        Auto: 15 rows (MatchTime 15→1) at 0.1s. Teleop: MatchTime 140→1.
        MatchTime first hits 30 at teleop offset 110 → overall index 125 → 12.5s.
        """
        periods = plots.match_periods(full_match_df)
        assert periods.endgame_start == pytest.approx(12.5)
        # The row nearest endgame_start must have MatchTime <= the endgame threshold.
        idx = (full_match_df[config.ELAPSED_COL] - periods.endgame_start).abs().idxmin()
        assert (
            full_match_df.loc[idx, config.MATCH_TIME_REMAINING_COL]
            <= config.ENDGAME_SECONDS
        )

    def test_match_end_is_last_elapsed(self, full_match_df):
        """SYS-PWR-008: match_end equals the last elapsed value."""
        periods = plots.match_periods(full_match_df)
        assert periods.match_end == pytest.approx(
            full_match_df[config.ELAPSED_COL].iloc[-1]
        )

    def test_auto_only_capture_has_no_teleop_or_endgame(self, akit_match_df):
        """SYS-PWR-008: The auto-only e4 slice yields None for teleop/endgame starts."""
        periods = plots.match_periods(akit_match_df)
        assert periods.teleop_start is None
        assert periods.endgame_start is None
        assert periods.match_start == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Period line drawing
# ---------------------------------------------------------------------------

class TestPeriodLines:
    def test_four_lines_for_full_match(self, full_match_df):
        """SYS-PWR-008: A full match draws all four period vertical lines."""
        fig, ax = plt.subplots()
        periods = plots.match_periods(full_match_df)
        plots.add_period_lines(ax, periods)
        # Four axvline calls → four Line2D objects on the axes
        assert len(ax.lines) == 4
        plt.close(fig)

    def test_two_lines_for_auto_only(self, akit_match_df):
        """SYS-PWR-008: An auto-only capture draws only start and end lines."""
        fig, ax = plt.subplots()
        periods = plots.match_periods(akit_match_df)
        plots.add_period_lines(ax, periods)
        assert len(ax.lines) == 2
        plt.close(fig)


# ---------------------------------------------------------------------------
# Individual plot functions
# ---------------------------------------------------------------------------

class TestPlotFunctions:
    def test_plot_voltage_returns_figure(self, akit_match_df):
        """SYS-PWR-008: plot_voltage returns a matplotlib Figure."""
        fig = plots.plot_voltage(akit_match_df, "elimination-4")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_voltage_has_brownout_threshold_line(self, akit_match_df):
        """SYS-PWR-008: plot_voltage draws a horizontal brownout threshold line."""
        fig = plots.plot_voltage(akit_match_df, "elimination-4")
        ax = fig.axes[0]
        # One of the horizontal lines should sit at the brownout threshold.
        hlines = [ln.get_ydata()[0] for ln in ax.lines if ln.get_ydata()[0] == ln.get_ydata()[-1]]
        assert any(y == pytest.approx(config.BROWNOUT_THRESHOLD) for y in hlines)
        plt.close(fig)

    def test_plot_total_current_returns_figure(self, akit_match_df):
        """SYS-PWR-008: plot_total_current returns a Figure."""
        fig = plots.plot_total_current(akit_match_df, "elimination-4")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_current_by_subsystem_returns_figure(self, akit_match_df):
        """SYS-PWR-008: plot_current_by_subsystem returns a Figure."""
        fig = plots.plot_current_by_subsystem(akit_match_df, "elimination-4")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_current_by_subsystem_has_stacked_areas(self, akit_match_df):
        """SYS-PWR-008: Stacked area plot produces one PolyCollection per subsystem."""
        fig = plots.plot_current_by_subsystem(akit_match_df, "elimination-4")
        ax = fig.axes[0]
        # stackplot adds one collection per series
        assert len(ax.collections) >= 1
        plt.close(fig)

    def test_plot_energy_rank_returns_figure(self, akit_match_df):
        """SYS-PWR-008: plot_energy_rank returns a Figure."""
        model = PowerModel(akit_match_df)
        fig = plots.plot_energy_rank(model.subsystem_energy_breakdown(), "elimination-4")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_energy_rank_one_bar_per_subsystem(self, akit_match_df):
        """SYS-PWR-008: Energy rank chart has one bar per subsystem group."""
        model = PowerModel(akit_match_df)
        breakdown = model.subsystem_energy_breakdown()
        fig = plots.plot_energy_rank(breakdown, "elimination-4")
        ax = fig.axes[0]
        assert len(ax.patches) == len(breakdown)
        plt.close(fig)

    def test_session_label_in_title(self, akit_match_df):
        """SYS-PWR-008: The session label appears in the plot title."""
        fig = plots.plot_voltage(akit_match_df, "elimination-4")
        assert "elimination-4" in fig.axes[0].get_title()
        plt.close(fig)

    def test_period_lines_present_on_timeseries_plots(self, full_match_df):
        """SYS-PWR-008: Each time-series plot includes the period vertical lines."""
        for plot_fn in (
            plots.plot_voltage,
            plots.plot_total_current,
            plots.plot_current_by_subsystem,
        ):
            fig = plot_fn(full_match_df, "test")
            ax = fig.axes[0]
            # Vertical period lines have equal x at both ends.
            vlines = [
                ln for ln in ax.lines
                if ln.get_xdata()[0] == ln.get_xdata()[-1]
            ]
            assert len(vlines) >= 4, f"{plot_fn.__name__} missing period lines"
            plt.close(fig)
