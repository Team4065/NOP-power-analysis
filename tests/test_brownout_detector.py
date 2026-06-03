"""Tests for BrownoutDetector.

Requirements covered:
  SYS-PWR-007: Brownout event detection and characterization

Two detection paths:
  1. Preferred — use the browned_out boolean column (from /SystemStats/BrownedOut)
  2. Fallback — threshold the voltage column when browned_out is absent
"""

from __future__ import annotations

import pandas as pd
import pytest

from power_analysis import config
from power_analysis.analysis.brownout_detector import BrownoutDetector


def _akit_df(
    voltage: list[float],
    browned_out: list[bool] | None = None,
    dt: float = 0.02,
) -> pd.DataFrame:
    """Build a minimal AKit-normalized DataFrame with optional browned_out flags."""
    n = len(voltage)
    if browned_out is None:
        browned_out = [False] * n
    return pd.DataFrame({
        config.ELAPSED_COL: [i * dt for i in range(n)],
        config.VOLTAGE_12V_COL: voltage,
        config.BROWNED_OUT_OUT_COL: browned_out,
    })


# ---------------------------------------------------------------------------
# BrownedOut-signal path
# ---------------------------------------------------------------------------

class TestBrownedOutSignal:
    def test_no_brownout_when_signal_all_false(self):
        """SYS-PWR-007: No events when browned_out is always False."""
        df = _akit_df(voltage=[12.0] * 10, browned_out=[False] * 10)
        detector = BrownoutDetector(df)
        assert detector.brownout_count() == 0

    def test_single_brownout_event_detected(self):
        """SYS-PWR-007: One contiguous browned_out=True block is one event."""
        df = _akit_df(
            voltage=[12.0, 12.0, 5.5, 5.0, 5.8, 12.0, 12.0],
            browned_out=[False, False, True, True, True, False, False],
        )
        detector = BrownoutDetector(df)
        assert detector.brownout_count() == 1

    def test_two_separate_brownout_events(self):
        """SYS-PWR-007: Two separate browned_out blocks are two events."""
        df = _akit_df(
            voltage=[12.0, 5.0, 12.0, 12.0, 5.0, 5.0, 12.0],
            browned_out=[False, True, False, False, True, True, False],
        )
        detector = BrownoutDetector(df)
        assert detector.brownout_count() == 2

    def test_detect_returns_event_rows_with_columns(self):
        """SYS-PWR-007: detect() returns a DataFrame with the expected columns."""
        df = _akit_df(
            voltage=[12.0, 5.0, 5.0, 12.0],
            browned_out=[False, True, True, False],
        )
        detector = BrownoutDetector(df)
        events = detector.detect()
        assert isinstance(events, pd.DataFrame)
        for col in ("start_time", "end_time", "duration_s", "min_voltage"):
            assert col in events.columns

    def test_event_duration_and_min_voltage(self):
        """SYS-PWR-007: Event duration and min voltage are computed correctly."""
        # browned_out True at elapsed 0.02 and 0.04 → duration 0.02s
        df = _akit_df(
            voltage=[12.0, 5.5, 5.0, 12.0],
            browned_out=[False, True, True, False],
            dt=0.02,
        )
        detector = BrownoutDetector(df)
        events = detector.detect()
        assert len(events) == 1
        row = events.iloc[0]
        assert row["start_time"] == pytest.approx(0.02)
        assert row["end_time"] == pytest.approx(0.04)
        assert row["duration_s"] == pytest.approx(0.02)
        assert row["min_voltage"] == pytest.approx(5.0)

    def test_total_brownout_duration(self):
        """SYS-PWR-007: total_brownout_duration sums all event durations."""
        df = _akit_df(
            voltage=[12.0, 5.0, 5.0, 12.0, 5.0, 5.0, 12.0],
            browned_out=[False, True, True, False, True, True, False],
            dt=0.02,
        )
        detector = BrownoutDetector(df)
        # two events, each 0.02s duration
        assert detector.total_brownout_duration() == pytest.approx(0.04)


# ---------------------------------------------------------------------------
# Threshold fallback path (legacy / no browned_out column)
# ---------------------------------------------------------------------------

class TestThresholdFallback:
    def test_threshold_used_when_no_browned_out_column(self):
        """SYS-PWR-007: Falls back to voltage threshold when browned_out absent."""
        df = pd.DataFrame({
            config.ELAPSED_COL: [0.0, 0.02, 0.04, 0.06],
            config.VOLTAGE_12V_COL: [12.0, 5.0, 5.0, 12.0],
        })
        detector = BrownoutDetector(df, threshold=6.0)
        assert detector.brownout_count() == 1

    def test_default_threshold_is_six_volts(self):
        """SYS-PWR-007: Default threshold is config.BROWNOUT_THRESHOLD (6.0V)."""
        df = pd.DataFrame({
            config.ELAPSED_COL: [0.0, 0.02, 0.04],
            config.VOLTAGE_12V_COL: [12.0, 5.5, 12.0],
        })
        detector = BrownoutDetector(df)
        assert detector.threshold == config.BROWNOUT_THRESHOLD
        assert detector.brownout_count() == 1


# ---------------------------------------------------------------------------
# Real match data
# ---------------------------------------------------------------------------

class TestRealMatch:
    def test_real_match_no_crash(self):
        """SYS-PWR-007: Detector runs on real match data without error."""
        from pathlib import Path

        from power_analysis.parsers.akit_parser import AKitParser

        fixture = Path(__file__).parent / "fixtures" / "akit_e4_slice.csv"
        df = AKitParser(fixture).load()
        detector = BrownoutDetector(df)
        count = detector.brownout_count()
        assert count >= 0  # cmptx_e4 had no brownouts; just verify it runs
