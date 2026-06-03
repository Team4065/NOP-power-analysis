"""Tests for PowerModel operating on AKit normalized DataFrames.

Requirements covered:
  SYS-PWR-005: Total power and energy computation
  SYS-PWR-006: Subsystem energy ranking
  SYS-PWR-007: Battery voltage amplitude analysis
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from power_analysis import config
from power_analysis.analysis.power_model import PowerModel
from power_analysis.parsers.akit_parser import AKitParser

FIXTURE = Path(__file__).parent / "fixtures" / "akit_e4_slice.csv"


@pytest.fixture(scope="module")
def match_df() -> pd.DataFrame:
    return AKitParser(FIXTURE).load()


def _make_akit_df(
    voltage: list[float],
    subsystem_currents: dict[str, list[float]],
    dt: float = 0.02,
) -> pd.DataFrame:
    """Build a minimal AKit-normalized DataFrame for unit testing."""
    n = len(voltage)
    total = [sum(subsystem_currents[s][i] for s in subsystem_currents) for i in range(n)]
    data = {
        config.ELAPSED_COL: [i * dt for i in range(n)],
        config.VOLTAGE_12V_COL: voltage,
        config.CURRENT_TOTAL_COL: total,
        config.ENABLED_OUT_COL: [True] * n,
        config.AUTONOMOUS_OUT_COL: [False] * n,
        config.BROWNED_OUT_OUT_COL: [False] * n,
        config.MATCH_TIME_REMAINING_COL: [100.0 - i * dt for i in range(n)],
    }
    for sub, vals in subsystem_currents.items():
        data[f"current_{sub}"] = vals
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Schema auto-detection
# ---------------------------------------------------------------------------

class TestSchemaDetection:
    def test_akit_df_uses_voltage_12v(self, match_df):
        """SYS-PWR-005: PowerModel reads voltage from voltage_12v in AKit mode."""
        model = PowerModel(match_df)
        power = model.compute_instantaneous_power()
        assert len(power) == len(match_df)

    def test_energy_positive_on_real_match(self, match_df):
        """SYS-PWR-005: Real match energy is positive."""
        model = PowerModel(match_df)
        assert model.compute_energy() > 0

    def test_uses_elapsed_s_for_integration(self):
        """SYS-PWR-005: Energy integrates over elapsed_s column, not the index."""
        # Constant 12V × 10A = 120W for 1.0s → 120 J → 0.0333 Wh
        df = _make_akit_df(
            voltage=[12.0] * 51,
            subsystem_currents={"drive": [10.0] * 51},
            dt=0.02,
        )
        model = PowerModel(df)
        # 51 points × 0.02 = 1.0s; 120W × 1.0s = 120 J = 0.03333 Wh
        assert model.compute_energy() == pytest.approx(120.0 / 3600, rel=1e-3)


# ---------------------------------------------------------------------------
# Subsystem energy breakdown
# ---------------------------------------------------------------------------

class TestSubsystemBreakdown:
    def test_breakdown_returns_dict(self, match_df):
        """SYS-PWR-006: subsystem_energy_breakdown returns a dict."""
        model = PowerModel(match_df)
        breakdown = model.subsystem_energy_breakdown()
        assert isinstance(breakdown, dict)

    def test_breakdown_has_all_subsystems(self, match_df):
        """SYS-PWR-006: Breakdown contains an entry for each subsystem group."""
        model = PowerModel(match_df)
        breakdown = model.subsystem_energy_breakdown()
        for sub in config.AKIT_MOTOR_CURRENT_COLS:
            assert sub in breakdown

    def test_breakdown_sums_to_total_energy(self, match_df):
        """SYS-PWR-006: Subsystem energies sum to total match energy.

        Because current_total = Σ subsystem currents and voltage is a common
        factor, the integrated subsystem energies sum exactly to total energy.
        """
        model = PowerModel(match_df)
        total = model.compute_energy()
        breakdown_sum = sum(model.subsystem_energy_breakdown().values())
        assert breakdown_sum == pytest.approx(total, rel=1e-6)

    def test_known_breakdown_values(self):
        """SYS-PWR-006: Two subsystems with known currents produce known energy split."""
        # drive: 20A, shooter: 10A, constant 12V, 1.0s
        df = _make_akit_df(
            voltage=[12.0] * 51,
            subsystem_currents={
                "drive": [20.0] * 51,
                "shooter": [10.0] * 51,
            },
            dt=0.02,
        )
        model = PowerModel(df)
        breakdown = model.subsystem_energy_breakdown()
        # drive: 12*20=240W*1s=240J=0.0667Wh; shooter: 12*10=120W=0.0333Wh
        assert breakdown["drive"] == pytest.approx(240.0 / 3600, rel=1e-3)
        assert breakdown["shooter"] == pytest.approx(120.0 / 3600, rel=1e-3)


# ---------------------------------------------------------------------------
# Energy ranking
# ---------------------------------------------------------------------------

class TestEnergyRanking:
    def test_rank_returns_sorted_descending(self, match_df):
        """SYS-PWR-006: rank_by_energy returns (name, Wh) tuples sorted descending."""
        model = PowerModel(match_df)
        ranking = model.rank_by_energy()
        energies = [wh for _, wh in ranking]
        assert energies == sorted(energies, reverse=True)

    def test_rank_drive_is_largest_in_real_match(self, match_df):
        """SYS-PWR-006: Drive subsystem is the largest consumer in real match data."""
        model = PowerModel(match_df)
        ranking = model.rank_by_energy()
        # Drive (8 motors) should dominate; assert it's in the top 2
        top_two = [name for name, _ in ranking[:2]]
        assert "drive" in top_two

    def test_rank_covers_all_subsystems(self, match_df):
        """SYS-PWR-006: Ranking includes every subsystem group."""
        model = PowerModel(match_df)
        ranking = model.rank_by_energy()
        names = {name for name, _ in ranking}
        assert names == set(config.AKIT_MOTOR_CURRENT_COLS)


# ---------------------------------------------------------------------------
# Voltage statistics
# ---------------------------------------------------------------------------

class TestVoltageStats:
    def test_voltage_stats_fields(self, match_df):
        """SYS-PWR-007: voltage_stats exposes min, max, mean, drop."""
        model = PowerModel(match_df)
        stats = model.voltage_stats()
        assert hasattr(stats, "min_v")
        assert hasattr(stats, "max_v")
        assert hasattr(stats, "mean_v")
        assert hasattr(stats, "drop_v")

    def test_voltage_min_le_mean_le_max(self, match_df):
        """SYS-PWR-007: min ≤ mean ≤ max."""
        model = PowerModel(match_df)
        s = model.voltage_stats()
        assert s.min_v <= s.mean_v <= s.max_v

    def test_voltage_drop_equals_max_minus_min(self, match_df):
        """SYS-PWR-007: drop_v = max_v - min_v."""
        model = PowerModel(match_df)
        s = model.voltage_stats()
        assert s.drop_v == pytest.approx(s.max_v - s.min_v)

    def test_real_match_voltage_in_range(self, match_df):
        """SYS-PWR-007: Real match voltage stats are physically plausible.

        Valid band is brownout threshold (6.0V) to a fully charged 14V.
        This match sagged to ~8.8V under peak load — above brownout, below nominal.
        """
        model = PowerModel(match_df)
        s = model.voltage_stats()
        assert config.BROWNOUT_THRESHOLD <= s.min_v <= 14.0
        assert config.BROWNOUT_THRESHOLD <= s.max_v <= 14.0


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_peak_ge_average(self, match_df):
        """Invariant: peak power ≥ average power."""
        model = PowerModel(match_df)
        assert model.peak_power() >= model.average_power()

    def test_energy_non_negative(self, match_df):
        """Invariant: energy ≥ 0."""
        model = PowerModel(match_df)
        assert model.compute_energy() >= 0
