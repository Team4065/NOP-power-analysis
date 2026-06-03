"""Shared pytest fixtures and test-wide configuration.

Forces the non-interactive Agg matplotlib backend so plot tests run headlessly
on any platform (CI, airplane, etc.) without a windowing system.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must run before any pyplot import

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from power_analysis.parsers.akit_parser import AKitParser  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"
AKIT_FIXTURE = FIXTURE_DIR / "akit_e4_slice.csv"


@pytest.fixture(scope="session")
def akit_match_df() -> pd.DataFrame:
    """Parsed, normalized DataFrame for one real match window (cmptx_e4 slice)."""
    return AKitParser(AKIT_FIXTURE).load()
