"""Command-line entry point for the power analysis tool.

Usage:
    frc-power --log-dir <dir> [--match-type all|practice|qual|elim]
              [--match-number N] [--output-dir ./reports] [--no-plots]

Discovers AdvantageKit logs in --log-dir (converting any unpaired .wpilog to
.csv), then for each matching session: parses the match window, computes power
and energy, prints a ranked summary table, and saves the four analysis plots.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from power_analysis import config
from power_analysis.analysis.brownout_detector import BrownoutDetector
from power_analysis.analysis.power_model import PowerModel
from power_analysis.parsers.akit_ingester import AKitIngester, LogFile
from power_analysis.parsers.akit_parser import AKitParser
from power_analysis.utils.logger import get_logger

log = get_logger(__name__)

# Map the --match-type CLI choice to the set of MatchType integers it selects.
_MATCH_TYPE_FILTER = {
    "all": None,
    "practice": {0, 1},
    "qual": {2},
    "elim": {3},
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="frc-power",
        description="FRC Team 4065 telemetry power analysis tool.",
    )
    p.add_argument(
        "--log-dir", "-l",
        type=Path,
        required=True,
        help="Directory containing AdvantageKit .wpilog and/or .csv files.",
    )
    p.add_argument(
        "--match-type", "-t",
        choices=sorted(_MATCH_TYPE_FILTER),
        default="all",
        help="Filter by session type (default: all).",
    )
    p.add_argument(
        "--match-number", "-n",
        type=int,
        default=None,
        help="Filter to a specific match number.",
    )
    p.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("reports"),
        help="Directory for saved plot PNGs (default: ./reports).",
    )
    p.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation; print summary tables only.",
    )
    return p


def filter_logs(
    logs: list[LogFile], match_type: str, match_number: int | None
) -> list[LogFile]:
    """Filter discovered logs by session type and match number."""
    allowed_types = _MATCH_TYPE_FILTER[match_type]
    result = []
    for lf in logs:
        if allowed_types is not None and lf.match_type not in allowed_types:
            continue
        if match_number is not None and lf.match_number != match_number:
            continue
        result.append(lf)
    return result


def format_summary_table(session_label: str, model: PowerModel,
                         brownout: BrownoutDetector) -> str:
    """Build the per-match summary table as a string."""
    energy = model.subsystem_energy_breakdown()
    peaks = model.subsystem_peak_current()
    total_energy = sum(energy.values())

    lines = []
    sep = "─" * 56
    lines.append(f"Session: {session_label}")
    lines.append(sep)
    lines.append(f"{'Subsystem':<12} │ {'Peak (A)':>9} │ {'Energy (Wh)':>11} │ {'% Total':>7}")
    lines.append(sep)

    # Rank rows by energy, descending.
    for name, wh in sorted(energy.items(), key=lambda kv: kv[1], reverse=True):
        pct = (100.0 * wh / total_energy) if total_energy else 0.0
        lines.append(
            f"{name:<12} │ {peaks[name]:>9.1f} │ {wh:>11.3f} │ {pct:>6.1f}%"
        )

    lines.append(sep)
    total_peak = float(model.df[config.CURRENT_TOTAL_COL].max())
    lines.append(
        f"{'TOTAL':<12} │ {total_peak:>9.1f} │ {total_energy:>11.3f} │ {100.0:>6.1f}%"
    )
    lines.append(sep)

    # Voltage and brownout summary
    vs = model.voltage_stats()
    lines.append(
        f"Battery voltage: min {vs.min_v:.2f}V  max {vs.max_v:.2f}V  "
        f"mean {vs.mean_v:.2f}V  drop {vs.drop_v:.2f}V"
    )
    n_brown = brownout.brownout_count()
    if n_brown:
        lines.append(
            f"Brownouts: {n_brown} event(s), "
            f"{brownout.total_brownout_duration():.2f}s total"
        )
    else:
        lines.append("Brownouts: 0 events")
    lines.append(
        "Note: total current is the sum of measured motor signals; "
        "unmeasured loads (radio, VRM, lights) are excluded."
    )
    return "\n".join(lines)


def save_plots(df, model: PowerModel, session_label: str, output_dir: Path) -> list[Path]:
    """Render and save the four analysis plots; return the saved paths."""
    # Imported here so --no-plots runs without importing matplotlib.
    from power_analysis.visualization import plots

    output_dir.mkdir(parents=True, exist_ok=True)
    breakdown = model.subsystem_energy_breakdown()

    figures = {
        "voltage": plots.plot_voltage(df, session_label),
        "total_current": plots.plot_total_current(df, session_label),
        "current_by_subsystem": plots.plot_current_by_subsystem(df, session_label),
        "energy_rank": plots.plot_energy_rank(breakdown, session_label),
    }

    saved = []
    for name, fig in figures.items():
        path = output_dir / f"{session_label}_{name}.png"
        fig.savefig(path, dpi=100)
        saved.append(path)
        # Free the figure to avoid accumulating memory across many matches.
        import matplotlib.pyplot as plt
        plt.close(fig)
    return saved


def analyze_log(log_file: LogFile, output_dir: Path, make_plots: bool) -> bool:
    """Analyze one log file: parse, summarize, plot. Returns True on success."""
    df = AKitParser(log_file.path).load()
    if df.empty:
        log.warning("No match window found in %s — skipping.", log_file.path.name)
        return False

    model = PowerModel(df)
    brownout = BrownoutDetector(df)

    print()
    print(format_summary_table(log_file.session_label, model, brownout))

    if make_plots:
        saved = save_plots(df, model, log_file.session_label, output_dir)
        print(f"Saved {len(saved)} plot(s) to {output_dir}/")
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.log_dir.is_dir():
        print(f"Error: --log-dir is not a directory: {args.log_dir}", file=sys.stderr)
        return 2

    ingester = AKitIngester(args.log_dir)

    # Convert any unpaired wpilog files first (best-effort; report and continue).
    pending = ingester.pending_conversions()
    if pending:
        print(f"Converting {len(pending)} wpilog file(s) to CSV...")
        try:
            ingester.convert_all()
        except ImportError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
            print("Continuing with already-converted CSV files only.", file=sys.stderr)

    logs = ingester.discover()
    logs = filter_logs(logs, args.match_type, args.match_number)

    if not logs:
        print(
            f"No matching logs found in {args.log_dir} "
            f"(type={args.match_type}, number={args.match_number}).",
            file=sys.stderr,
        )
        return 1

    print(f"Analyzing {len(logs)} session(s) from {args.log_dir}")
    analyzed = 0
    for log_file in logs:
        if analyze_log(log_file, args.output_dir, make_plots=not args.no_plots):
            analyzed += 1

    print()
    print(f"Done — analyzed {analyzed} of {len(logs)} session(s).")
    return 0 if analyzed else 1


if __name__ == "__main__":
    sys.exit(main())
