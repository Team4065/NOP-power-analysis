"""Tests for PowerModel.

These tests will raise NotImplementedError until students implement the model.
Run with: pytest tests/test_power_model.py
"""

import pandas as pd
import pytest

from power_analysis import config
from power_analysis.analysis.power_model import PowerModel


def _make_df(voltage: list[float], current: list[float], enabled: list[bool] | None = None) -> pd.DataFrame:
    """Build a minimal telemetry DataFrame for testing."""
    n = len(voltage)
    if enabled is None:
        enabled = [True] * n
    return pd.DataFrame(
        {
            config.TIMESTAMP_COL: [i * 0.02 for i in range(n)],
            config.VOLTAGE_COL: voltage,
            config.CURRENT_COL: current,
            config.ENABLED_COL: enabled,
        }
    ).set_index(config.TIMESTAMP_COL)


def test_instantaneous_power_values():
    """Power should equal voltage × current at every row."""
    df = _make_df([12.0, 10.0, 8.0], [10.0, 20.0, 30.0])
    model = PowerModel(df)
    power = model.compute_instantaneous_power()
    assert list(power) == pytest.approx([120.0, 200.0, 240.0])


def test_energy_positive():
    """Energy should be a positive float for any active match."""
    df = _make_df([12.0] * 10, [20.0] * 10)
    model = PowerModel(df)
    assert model.compute_energy() > 0


def test_peak_power():
    """Peak power should be the maximum of voltage × current."""
    df = _make_df([12.0, 10.0, 8.0], [10.0, 20.0, 30.0])
    model = PowerModel(df)
    assert model.peak_power() == pytest.approx(240.0)


def test_average_power_enabled_only():
    """Average power should only consider enabled rows."""
    df = _make_df(
        voltage=[12.0, 12.0, 12.0, 12.0],
        current=[0.0, 20.0, 20.0, 0.0],
        enabled=[False, True, True, False],
    )
    model = PowerModel(df)
    # Only the two enabled rows (20 A × 12 V = 240 W each) should count
    assert model.average_power() == pytest.approx(240.0)
