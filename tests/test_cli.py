"""Tests for the command-line interface.

Requirements covered:
  SYS-PWR-001: Log directory ingestion (--log-dir)
  SYS-PWR-003: Session filtering by type / number
  SYS-PWR-008: Plot saving with session-labeled filenames
  SYS-PWR-009: CLI summary report table
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from power_analysis import cli
from power_analysis.parsers.akit_ingester import LogFile

FIXTURE = Path(__file__).parent / "fixtures" / "akit_e4_slice.csv"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class TestArgParsing:
    def test_log_dir_required(self):
        """SYS-PWR-001: --log-dir is required."""
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args([])

    def test_parses_log_dir(self):
        """SYS-PWR-001: --log-dir is parsed as a Path."""
        args = cli.build_parser().parse_args(["--log-dir", "/tmp/logs"])
        assert args.log_dir == Path("/tmp/logs")

    def test_defaults(self):
        """Defaults: match-type=all, output-dir=reports, plots enabled."""
        args = cli.build_parser().parse_args(["--log-dir", "/tmp/logs"])
        assert args.match_type == "all"
        assert args.match_number is None
        assert args.output_dir == Path("reports")
        assert args.no_plots is False

    def test_invalid_match_type_rejected(self):
        """--match-type only accepts known choices."""
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(["--log-dir", "/x", "--match-type", "bogus"])


# ---------------------------------------------------------------------------
# Log filtering
# ---------------------------------------------------------------------------

def _logs() -> list[LogFile]:
    return [
        LogFile(Path("a.csv"), "practice-session", 0, 0),
        LogFile(Path("b.csv"), "practice-match", 1, 1),
        LogFile(Path("c.csv"), "qual-12", 2, 12),
        LogFile(Path("d.csv"), "elimination-4", 3, 4),
    ]


class TestFilterLogs:
    def test_all_returns_everything(self):
        assert len(cli.filter_logs(_logs(), "all", None)) == 4

    def test_elim_filter(self):
        """SYS-PWR-003: 'elim' keeps only MatchType 3."""
        out = cli.filter_logs(_logs(), "elim", None)
        assert [lf.session_label for lf in out] == ["elimination-4"]

    def test_qual_filter(self):
        out = cli.filter_logs(_logs(), "qual", None)
        assert [lf.session_label for lf in out] == ["qual-12"]

    def test_practice_filter_includes_both_practice_types(self):
        """SYS-PWR-003: 'practice' keeps MatchType 0 and 1."""
        out = cli.filter_logs(_logs(), "practice", None)
        assert {lf.match_type for lf in out} == {0, 1}

    def test_match_number_filter(self):
        out = cli.filter_logs(_logs(), "all", 4)
        assert [lf.session_label for lf in out] == ["elimination-4"]

    def test_type_and_number_combined(self):
        out = cli.filter_logs(_logs(), "elim", 4)
        assert len(out) == 1
        out_none = cli.filter_logs(_logs(), "elim", 99)
        assert out_none == []


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

class TestSummaryTable:
    def test_table_contains_all_subsystems_and_total(self, akit_match_df):
        """SYS-PWR-009: Summary table lists every subsystem plus a TOTAL row."""
        from power_analysis.analysis.brownout_detector import BrownoutDetector
        from power_analysis.analysis.power_model import PowerModel

        model = PowerModel(akit_match_df)
        brownout = BrownoutDetector(akit_match_df)
        table = cli.format_summary_table("elimination-4", model, brownout)

        assert "elimination-4" in table
        for sub in ("drive", "shooter", "hopper", "intake", "climber"):
            assert sub in table
        assert "TOTAL" in table
        assert "Brownouts:" in table
        assert "unmeasured loads" in table

    def test_table_rows_ranked_by_energy(self, akit_match_df):
        """SYS-PWR-009: Subsystem rows appear in descending energy order."""
        from power_analysis.analysis.brownout_detector import BrownoutDetector
        from power_analysis.analysis.power_model import PowerModel

        model = PowerModel(akit_match_df)
        brownout = BrownoutDetector(akit_match_df)
        table = cli.format_summary_table("elimination-4", model, brownout)

        # drive dominates in real data → appears before shooter in the table
        assert table.index("drive") < table.index("shooter")


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_main_runs_and_saves_plots(self, tmp_path, capsys):
        """SYS-PWR-008/009: Full run produces a summary and four PNGs."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        shutil.copy(FIXTURE, log_dir / "akit_cmptx_e4.csv")
        out_dir = tmp_path / "reports"

        rc = cli.main([
            "--log-dir", str(log_dir),
            "--output-dir", str(out_dir),
        ])
        assert rc == 0

        captured = capsys.readouterr()
        assert "elimination-4" in captured.out
        assert "TOTAL" in captured.out

        pngs = sorted(out_dir.glob("*.png"))
        assert len(pngs) == 4
        names = {p.name for p in pngs}
        assert "elimination-4_voltage.png" in names
        assert "elimination-4_energy_rank.png" in names

    def test_main_no_plots_skips_pngs(self, tmp_path, capsys):
        """--no-plots prints the summary but writes no PNGs."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        shutil.copy(FIXTURE, log_dir / "akit_cmptx_e4.csv")
        out_dir = tmp_path / "reports"

        rc = cli.main([
            "--log-dir", str(log_dir),
            "--output-dir", str(out_dir),
            "--no-plots",
        ])
        assert rc == 0
        assert not out_dir.exists() or not list(out_dir.glob("*.png"))

    def test_main_bad_log_dir_returns_2(self, tmp_path):
        """A non-existent --log-dir returns exit code 2."""
        rc = cli.main(["--log-dir", str(tmp_path / "nope")])
        assert rc == 2

    def test_main_no_matching_logs_returns_1(self, tmp_path):
        """An empty (but valid) directory returns exit code 1."""
        empty = tmp_path / "empty"
        empty.mkdir()
        rc = cli.main(["--log-dir", str(empty)])
        assert rc == 1

    def test_main_match_number_filter_excludes(self, tmp_path):
        """Filtering to a non-present match number yields exit code 1."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        shutil.copy(FIXTURE, log_dir / "akit_cmptx_e4.csv")
        rc = cli.main([
            "--log-dir", str(log_dir),
            "--match-number", "99",
            "--no-plots",
        ])
        assert rc == 1
