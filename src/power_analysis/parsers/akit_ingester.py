"""Discover, classify, and convert FRC AdvantageKit log files.

Handles two file types in a user-supplied directory:
  .wpilog — binary DataLog; converted to .csv on demand via robotpy-wpiutil
  .csv    — either AKit sparse format or legacy flat schema

AKit CSV columns begin with "/" (e.g. "/SystemStats/BatteryVoltage").
Legacy flat CSVs use plain names (e.g. "voltage_battery").
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from power_analysis import config
from power_analysis.utils.logger import get_logger

log = get_logger(__name__)

# Match-time value that indicates no live match is running
_NO_MATCH_TIME = -1.0


@dataclass(frozen=True)
class LogFile:
    """Metadata for a single discovered AKit log file."""

    path: Path
    session_label: str
    match_type: int
    match_number: int


class AKitIngester:
    """Discover and classify AdvantageKit log files in a directory.

    Parameters
    ----------
    log_dir : Path
        Directory containing .wpilog and/or .csv files.

    Example
    -------
    >>> ingester = AKitIngester(Path("/path/to/championship_logs"))
    >>> ingester.convert_all()          # wpilog → csv for any unconverted files
    >>> log_files = ingester.discover() # list[LogFile]
    """

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = Path(log_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(self) -> list[LogFile]:
        """Return a LogFile entry for every AKit-format CSV in log_dir."""
        results: list[LogFile] = []
        for csv_path in sorted(self.log_dir.glob("*.csv")):
            if not self.is_akit_format(csv_path):
                log.debug("Skipping non-AKit CSV: %s", csv_path.name)
                continue
            match_type, match_number = self._read_match_identity(csv_path)
            label = self._build_label(match_type, match_number, csv_path)
            results.append(LogFile(
                path=csv_path,
                session_label=label,
                match_type=match_type,
                match_number=match_number,
            ))
        return results

    def pending_conversions(self) -> list[Path]:
        """Return .wpilog files that have no paired .csv yet."""
        pending = []
        for wpilog in sorted(self.log_dir.glob("*.wpilog")):
            paired_csv = wpilog.with_suffix(".csv")
            if not paired_csv.exists():
                pending.append(wpilog)
        return pending

    def convert_all(self) -> None:
        """Convert every pending .wpilog to .csv using robotpy-wpiutil.

        Silently skips files that already have a paired CSV.
        Raises ImportError if robotpy-wpiutil is not installed.
        """
        pending = self.pending_conversions()
        if not pending:
            log.info("No wpilog files need conversion.")
            return

        try:
            from power_analysis.parsers._wpilog_convert import convert_wpilog
        except ImportError as exc:
            raise ImportError(
                "robotpy-wpiutil is required to convert .wpilog files. "
                "Install it with: pip install robotpy-wpiutil"
            ) from exc

        for wpilog_path in pending:
            csv_path = wpilog_path.with_suffix(".csv")
            log.info("Converting %s → %s", wpilog_path.name, csv_path.name)
            rows, cols = convert_wpilog(wpilog_path, csv_path)
            log.info("  Done: %d rows, %d columns", rows, cols)

    # ------------------------------------------------------------------
    # Format detection
    # ------------------------------------------------------------------

    @staticmethod
    def is_akit_format(csv_path: Path) -> bool:
        """Return True if the CSV uses AKit hierarchical column names (contain '/')."""
        try:
            with csv_path.open(newline="") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
            return any("/" in h for h in headers)
        except (OSError, StopIteration):
            return False

    # ------------------------------------------------------------------
    # Session labeling
    # ------------------------------------------------------------------

    def _read_match_identity(self, csv_path: Path) -> tuple[int, int]:
        """Read MatchType and MatchNumber from the first non-empty data row."""
        type_col = config.AKIT_MATCH_TYPE_COL
        num_col = config.AKIT_MATCH_NUMBER_COL
        time_col = config.AKIT_MATCH_TIME_COL

        match_type = 0
        match_number = 0
        match_time_ever_valid = False

        try:
            # Read only the columns we need — efficient for large CSVs
            df = pd.read_csv(
                csv_path,
                usecols=lambda c: c in {type_col, num_col, time_col},
                dtype=str,
            )
        except (OSError, ValueError):
            return 0, 0

        for col in (type_col, num_col, time_col):
            if col not in df.columns:
                df[col] = ""

        df = df.ffill()

        for _, row in df.iterrows():
            try:
                mt = float(row[time_col])
                if mt != _NO_MATCH_TIME:
                    match_time_ever_valid = True
                mtype = int(float(row[type_col]))
                mnum = int(float(row[num_col]))
                if mtype > 0:
                    match_type = mtype
                    match_number = mnum
                    break
            except (ValueError, TypeError):
                continue

        if not match_time_ever_valid:
            return 0, 0

        return match_type, match_number

    @staticmethod
    def _build_label(match_type: int, match_number: int, csv_path: Path) -> str:
        """Build a human-readable session label."""
        labels = config.MATCH_TYPE_LABELS

        if match_type == 0:
            return labels[0]  # "practice-session"
        if match_type == 1:
            return labels[1]  # "practice-match"
        if match_type == 2:
            return f"{labels[2]}-{match_number}"  # "qual-N"
        if match_type == 3:
            return f"{labels[3]}-{match_number}"  # "elimination-N"

        return f"unknown-type{match_type}"
