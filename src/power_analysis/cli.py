"""Command-line entry point for the power analysis tool.

Usage:
    python -m power_analysis.cli --input <path_to_csv>
    frc-power --input <path_to_csv>            # after editable install
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="frc-power",
        description="FRC Team 4065 telemetry power analysis tool.",
    )
    p.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to a telemetry CSV file (see docs/telemetry_schema.md).",
    )
    p.add_argument(
        "--season", "-s",
        type=int,
        default=2026,
        help="Competition season year (default: 2026).",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Print a summary power report to stdout.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()  # noqa: F841

    # TODO: Import TelemetryParser and load args.input
    # TODO: Run PowerModel, BatteryModel, and BrownoutDetector
    # TODO: If args.report, print a summary table with peak power, energy, brownout count, R_internal
    raise NotImplementedError("Implement cli.main()")


if __name__ == "__main__":
    main()
