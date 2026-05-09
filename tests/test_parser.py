"""Tests for TelemetryParser.

These tests will raise NotImplementedError until students implement the parser.
Run with: pytest tests/test_parser.py
"""

from pathlib import Path

import pytest

from power_analysis import config
from power_analysis.parsers.telemetry_parser import TelemetryParser

SAMPLE_CSV = config.SAMPLE_DIR / "2026_sample_match_1.csv"


def test_load_returns_dataframe():
    """load() should return a DataFrame with timestamp as the index."""
    parser = TelemetryParser(SAMPLE_CSV)
    df = parser.load()
    assert df.index.name == config.TIMESTAMP_COL


def test_load_has_required_columns():
    """Loaded DataFrame must contain all required columns."""
    parser = TelemetryParser(SAMPLE_CSV)
    df = parser.load()
    for col in config.REQUIRED_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_load_file_not_found():
    """load() should raise FileNotFoundError for a non-existent path."""
    parser = TelemetryParser("does_not_exist.csv")
    with pytest.raises(FileNotFoundError):
        parser.load()


def test_load_missing_column(tmp_path: Path):
    """load() should raise ValueError when a required column is absent."""
    bad_csv = tmp_path / "bad.csv"
    # Write a CSV that is missing the voltage column
    bad_csv.write_text("timestamp,robot_enabled,current_total\n0.0,True,5.0\n")
    parser = TelemetryParser(bad_csv)
    with pytest.raises(ValueError):
        parser.load()
