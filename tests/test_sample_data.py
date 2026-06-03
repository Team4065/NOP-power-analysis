"""Verify the committed AdvantageKit sample in data/sample/.

data/sample/ holds a real AdvantageKit match sample (akit_*.csv with a paired
.wpilog) so peers and students can run the tool end-to-end. Legacy flat-schema
parsing is covered separately by tests/test_parser.py with its own temp data.
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
AKIT_CSVS = [p for p in ALL_CSVS if _is_akit(p)]


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
    """Each AKit sample must parse into a non-empty, in-range match window."""
    from power_analysis.parsers.akit_parser import AKitParser

    df = AKitParser(csv_path).load()
    assert len(df) >= 10, f"{csv_path.name} parsed to only {len(df)} match rows"
    assert df[config.VOLTAGE_12V_COL].between(0, 15).all()
