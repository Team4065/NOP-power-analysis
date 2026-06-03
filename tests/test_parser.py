"""Tests for the legacy flat-schema TelemetryParser.

These build their own flat-schema CSV in a temp directory, so the parser is
covered without relying on any committed sample data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from power_analysis import config
from power_analysis.parsers.telemetry_parser import TelemetryParser

_HEADER = "timestamp,match_time,robot_enabled,autonomous,voltage_battery,current_total"
_ROWS = "\n".join(
    f"{i * 0.02:.2f},{15 - i * 0.02:.2f},True,True,12.4,{10.0 + i}"
    for i in range(12)
)


@pytest.fixture
def flat_csv(tmp_path: Path) -> Path:
    """A minimal valid legacy flat-schema telemetry CSV."""
    path = tmp_path / "flat_match.csv"
    path.write_text(_HEADER + "\n" + _ROWS + "\n")
    return path


def test_load_returns_dataframe(flat_csv):
    """load() should return a DataFrame with timestamp as the index."""
    df = TelemetryParser(flat_csv).load()
    assert df.index.name == config.TIMESTAMP_COL


def test_load_has_required_columns(flat_csv):
    """Loaded DataFrame must contain all required columns."""
    df = TelemetryParser(flat_csv).load()
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
    # Missing the voltage column.
    bad_csv.write_text("timestamp,robot_enabled,current_total\n0.0,True,5.0\n")
    parser = TelemetryParser(bad_csv)
    with pytest.raises(ValueError):
        parser.load()
