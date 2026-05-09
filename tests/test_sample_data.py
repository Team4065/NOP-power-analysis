"""Verify that sample CSV files exist and conform to the telemetry schema."""

from pathlib import Path

import pandas as pd
import pytest

from power_analysis import config

SAMPLE_FILES = list(config.SAMPLE_DIR.glob("*.csv"))


def test_sample_files_exist():
    """At least two sample files must be present."""
    assert len(SAMPLE_FILES) >= 2, (
        f"Expected >=2 sample CSVs in {config.SAMPLE_DIR}, found {len(SAMPLE_FILES)}"
    )


@pytest.mark.parametrize("csv_path", SAMPLE_FILES)
def test_sample_has_required_columns(csv_path: Path):
    """Each sample CSV must contain all required columns."""
    df = pd.read_csv(csv_path)
    missing = [c for c in config.REQUIRED_COLS if c not in df.columns]
    assert not missing, f"{csv_path.name} is missing columns: {missing}"


@pytest.mark.parametrize("csv_path", SAMPLE_FILES)
def test_sample_has_rows(csv_path: Path):
    """Each sample CSV must contain at least 10 rows of data."""
    df = pd.read_csv(csv_path)
    assert len(df) >= 10, f"{csv_path.name} has only {len(df)} rows"


@pytest.mark.parametrize("csv_path", SAMPLE_FILES)
def test_voltage_in_plausible_range(csv_path: Path):
    """Battery voltage should stay between 0 V and 15 V."""
    df = pd.read_csv(csv_path)
    assert df[config.VOLTAGE_COL].between(0, 15).all(), (
        f"{csv_path.name}: voltage values outside 0–15 V range"
    )
