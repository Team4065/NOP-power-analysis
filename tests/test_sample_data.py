"""Verify that sample data files exist and conform to their schema.

data/sample/ holds two kinds of files:
  * legacy flat-schema synthetic CSVs (2026_sample_match_*.csv)
  * a real AdvantageKit match sample (akit_*.csv, with a paired .wpilog)

Each kind is validated against its own schema.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from power_analysis import config


def _is_akit(csv_path: Path) -> bool:
    """True if the CSV uses AKit hierarchical ('/'-prefixed) column names."""
    with csv_path.open(newline="") as f:
        headers = next(csv.reader(f), [])
    return any("/" in h for h in headers)


ALL_CSVS = sorted(config.SAMPLE_DIR.glob("*.csv"))
LEGACY_CSVS = [p for p in ALL_CSVS if not _is_akit(p)]
AKIT_CSVS = [p for p in ALL_CSVS if _is_akit(p)]


def test_sample_files_exist():
    """At least two sample CSVs must be present."""
    assert len(ALL_CSVS) >= 2, (
        f"Expected >=2 sample CSVs in {config.SAMPLE_DIR}, found {len(ALL_CSVS)}"
    )


# ---------------------------------------------------------------------------
# Legacy flat-schema samples
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("csv_path", LEGACY_CSVS)
def test_legacy_sample_has_required_columns(csv_path: Path):
    """Each legacy CSV must contain all required flat-schema columns."""
    df = pd.read_csv(csv_path)
    missing = [c for c in config.REQUIRED_COLS if c not in df.columns]
    assert not missing, f"{csv_path.name} is missing columns: {missing}"


@pytest.mark.parametrize("csv_path", LEGACY_CSVS)
def test_legacy_sample_voltage_in_range(csv_path: Path):
    """Legacy sample battery voltage should stay between 0 V and 15 V."""
    df = pd.read_csv(csv_path)
    assert df[config.VOLTAGE_COL].between(0, 15).all(), (
        f"{csv_path.name}: voltage values outside 0–15 V range"
    )


# ---------------------------------------------------------------------------
# AKit match sample
# ---------------------------------------------------------------------------

def test_akit_sample_present():
    """A committed AKit sample (with a paired .wpilog) must exist for tool review."""
    assert AKIT_CSVS, "Expected at least one AKit-format sample CSV in data/sample/"
    for csv_path in AKIT_CSVS:
        assert csv_path.with_suffix(".wpilog").exists(), (
            f"{csv_path.name} has no paired .wpilog"
        )


@pytest.mark.parametrize("csv_path", AKIT_CSVS)
def test_akit_sample_has_voltage_signal(csv_path: Path):
    """Each AKit sample must carry the battery voltage signal."""
    df = pd.read_csv(csv_path, nrows=5)
    assert config.AKIT_VOLTAGE_COL in df.columns


@pytest.mark.parametrize("csv_path", AKIT_CSVS)
def test_akit_sample_parses_to_match_window(csv_path: Path):
    """Each AKit sample must parse into a non-empty match window."""
    from power_analysis.parsers.akit_parser import AKitParser

    df = AKitParser(csv_path).load()
    assert len(df) >= 10, f"{csv_path.name} parsed to only {len(df)} match rows"
    assert df[config.VOLTAGE_12V_COL].between(0, 15).all()
