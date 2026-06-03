"""Tests for AKitIngester — file discovery, format detection, session labeling.

Requirements covered:
  SYS-PWR-001: Log directory ingestion
  SYS-PWR-002: Automatic wpilog conversion (discovery / pairing logic only;
               actual wpilog byte-level conversion is tested separately)
  SYS-PWR-003: Session type detection and labeling
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from power_analysis.parsers.akit_ingester import AKitIngester, LogFile


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FIXTURE_AKIT = Path(__file__).parent / "fixtures" / "akit_e4_slice.csv"


def _write_minimal_akit_csv(path: Path, match_type: int, match_number: int) -> None:
    """Write a tiny AKit-format CSV (just enough columns for session detection)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "/DriverStation/MatchType",
            "/DriverStation/MatchNumber",
            "/DriverStation/MatchTime",
            "/SystemStats/BatteryVoltage",
        ])
        writer.writerow([1.0, match_type, match_number, 20.0, 12.5])
        writer.writerow([1.02, "", "", "", ""])


def _write_legacy_flat_csv(path: Path) -> None:
    """Write a legacy flat-schema CSV (no slash-prefixed column names)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "voltage_battery", "current_total", "robot_enabled"])
        writer.writerow([0.0, 12.5, 5.0, True])


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

class TestFormatDetection:
    def test_akit_fixture_detected_as_akit(self):
        """SYS-PWR-001: Real AKit fixture must be detected as AKit format."""
        ingester = AKitIngester(FIXTURE_AKIT.parent)
        assert ingester.is_akit_format(FIXTURE_AKIT)

    def test_legacy_csv_not_detected_as_akit(self, tmp_path):
        """SYS-PWR-001: Legacy flat-schema CSV must not be detected as AKit."""
        legacy = tmp_path / "legacy.csv"
        _write_legacy_flat_csv(legacy)
        ingester = AKitIngester(tmp_path)
        assert not ingester.is_akit_format(legacy)

    def test_empty_dir_returns_empty_list(self, tmp_path):
        """SYS-PWR-001: Empty directory yields no LogFile entries."""
        ingester = AKitIngester(tmp_path)
        assert ingester.discover() == []


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

class TestFileDiscovery:
    def test_discovers_akit_csv(self, tmp_path):
        """SYS-PWR-001: AKit CSV in target dir is discovered."""
        dst = tmp_path / "akit_match.csv"
        shutil.copy(FIXTURE_AKIT, dst)
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert len(files) == 1
        assert files[0].path == dst

    def test_discovers_multiple_csvs(self, tmp_path):
        """SYS-PWR-001: Multiple AKit CSVs are all discovered."""
        for name in ("akit_a.csv", "akit_b.csv"):
            shutil.copy(FIXTURE_AKIT, tmp_path / name)
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert len(files) == 2

    def test_skips_legacy_csv(self, tmp_path):
        """SYS-PWR-001: Legacy flat-schema CSVs are not included in AKit results."""
        _write_legacy_flat_csv(tmp_path / "legacy.csv")
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert files == []

    def test_wpilog_without_csv_listed_for_conversion(self, tmp_path):
        """SYS-PWR-002: A .wpilog with no paired .csv is flagged needs_conversion=True."""
        stub = tmp_path / "akit_match.wpilog"
        stub.write_bytes(b"\x00" * 16)  # stub binary file
        ingester = AKitIngester(tmp_path)
        pending = ingester.pending_conversions()
        assert len(pending) == 1
        assert pending[0] == stub

    def test_wpilog_with_paired_csv_not_flagged(self, tmp_path):
        """SYS-PWR-002: A .wpilog that already has a paired .csv is not re-converted."""
        stub = tmp_path / "akit_match.wpilog"
        stub.write_bytes(b"\x00" * 16)
        shutil.copy(FIXTURE_AKIT, tmp_path / "akit_match.csv")
        ingester = AKitIngester(tmp_path)
        assert ingester.pending_conversions() == []


# ---------------------------------------------------------------------------
# Session labeling
# ---------------------------------------------------------------------------

class TestSessionLabeling:
    @pytest.mark.parametrize("match_type,match_number,expected_label", [
        (3, 4,  "elimination-4"),
        (2, 12, "qual-12"),
        (1, 1,  "practice-match"),
        (0, 0,  "practice-session"),
    ])
    def test_session_label_from_match_type(
        self, tmp_path, match_type, match_number, expected_label
    ):
        """SYS-PWR-003: Session label derived correctly from MatchType/MatchNumber."""
        csv_path = tmp_path / f"akit_type{match_type}.csv"
        _write_minimal_akit_csv(csv_path, match_type, match_number)
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert len(files) == 1
        assert files[0].session_label == expected_label

    def test_real_fixture_labeled_elimination_4(self, tmp_path):
        """SYS-PWR-003: Real cmptx_e4 fixture gets label 'elimination-4'."""
        dst = tmp_path / "akit_cmptx_e4.csv"
        shutil.copy(FIXTURE_AKIT, dst)
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert files[0].session_label == "elimination-4"

    def test_missing_match_time_falls_back_to_practice_session(self, tmp_path):
        """SYS-PWR-003: MatchTime always -1 → practice-session label."""
        path = tmp_path / "akit_nmt.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "/DriverStation/MatchType",
                             "/DriverStation/MatchNumber", "/DriverStation/MatchTime",
                             "/SystemStats/BatteryVoltage"])
            writer.writerow([1.0, 0, 0, -1, 12.5])
            writer.writerow([1.02, "", "", -1, ""])
        ingester = AKitIngester(tmp_path)
        files = ingester.discover()
        assert files[0].session_label == "practice-session"


# ---------------------------------------------------------------------------
# LogFile data structure
# ---------------------------------------------------------------------------

class TestLogFileStructure:
    def test_logfile_has_required_fields(self, tmp_path):
        """LogFile named tuple/dataclass exposes path, session_label, match_type, match_number."""
        dst = tmp_path / "akit_e4.csv"
        shutil.copy(FIXTURE_AKIT, dst)
        ingester = AKitIngester(tmp_path)
        lf: LogFile = ingester.discover()[0]
        assert hasattr(lf, "path")
        assert hasattr(lf, "session_label")
        assert hasattr(lf, "match_type")
        assert hasattr(lf, "match_number")

    def test_logfile_path_is_pathlib_path(self, tmp_path):
        """LogFile.path must be a pathlib.Path, not a string."""
        dst = tmp_path / "akit_e4.csv"
        shutil.copy(FIXTURE_AKIT, dst)
        ingester = AKitIngester(tmp_path)
        lf = ingester.discover()[0]
        assert isinstance(lf.path, Path)
