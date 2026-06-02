# System Requirements

FRC Team 4065 Power Analysis Tool — system-level requirements.

Convention: **SHALL** = mandatory, **SHOULD** = strongly recommended, **MAY** = optional.
Each requirement is testable and traceable to an implementation module.

Changelog at bottom.

---

## Purpose

Provide FRC Team 4065 engineers with a command-line tool that ingests robot telemetry logs from competition and practice sessions, computes electrical power metrics from the 12V main battery, and produces ranked summaries and time-series plots that support robot performance analysis and battery management decisions.

## Scope

**In scope:**
- Processing AdvantageKit `.wpilog` and post-processed `.csv` files
- Single-match power analysis (one match window per invocation, or batch over a directory)
- Per-subsystem current draw and energy consumption
- Battery voltage amplitude analysis
- Plot generation with match-period annotations
- Cross-platform execution on Linux and Windows

**Out of scope (Phase 1):**
- Battery charge time prediction (deferred to Phase 7 — requires charging data not yet collected)
- Real-time telemetry (logs only)
- Multi-robot comparison
- Web-based dashboard (Streamlit deferred)

---

## Functional Requirements

### SYS-PWR-001 — Log directory ingestion

The tool SHALL accept a user-specified directory path (via `--log-dir` CLI argument) containing `.wpilog` files, `.csv` files, or both.

There SHALL be no hardcoded data path in source code.

### SYS-PWR-002 — Automatic wpilog conversion

For each `.wpilog` file in the specified directory that does not already have a paired `.csv` file, the tool SHALL automatically convert it to CSV using `robotpy-wpiutil`.

The tool SHALL also accept directories that contain only pre-converted `.csv` files (no wpilog required).

Converted CSV files SHALL be written to the same directory as the source wpilog, using the same base filename with a `.csv` extension.

The conversion SHALL run on both Linux and Windows without modification.

### SYS-PWR-003 — Session type detection and labeling

The tool SHALL detect the session type from log signals (`/DriverStation/MatchType`, `/DriverStation/MatchTime`) and assign a session label to each log file:

| Condition | Label |
|---|---|
| MatchType = 0 or MatchTime always -1 | `practice-session` |
| MatchType = 1 | `practice-match` |
| MatchType = 2 | `qual-{MatchNumber}` |
| MatchType = 3 | `elimination-{MatchNumber}` |

All output (plots, summary tables, filenames) SHALL include the session label.

The tool SHOULD process both practice and competition sessions; practice sessions SHOULD NOT be silently skipped.

### SYS-PWR-004 — Match window extraction

The tool SHALL extract the enabled match window from the log: the contiguous period where `/DriverStation/Enabled = True` and `/DriverStation/MatchTime > 0`.

The tool SHALL build an elapsed-time axis starting at 0 from the beginning of the auto period.

The tool SHALL handle the gap between auto end (Enabled briefly False) and teleop start (Enabled True again) by treating them as part of the same match window.

### SYS-PWR-005 — Total power and energy computation

The tool SHALL compute instantaneous power: `P(t) = V_battery(t) × I_total(t)` where:
- `V_battery` = `/SystemStats/BatteryVoltage`
- `I_total` = sum of all motor current signals across all subsystem groups

The tool SHALL compute total match energy via trapezoidal integration: `E = ∫ P dt` (result in Wh).

The tool SHALL note in all outputs that unmeasured loads (radio, VRM outputs, indicator lights) are excluded from the current sum.

### SYS-PWR-006 — Subsystem energy ranking

The tool SHALL compute per-subsystem energy consumption by integrating the summed current for each subsystem group over the match window (multiplied by battery voltage).

The tool SHALL produce a rank-ordered list of subsystems by total energy (Wh) with percentage of total.

Subsystem groups (see [GLOSSARY.md](GLOSSARY.md)):
- `drive` (8 motor signals)
- `shooter` (3 signals)
- `hopper` (3 signals)
- `intake` (2 signals)
- `climber` (1 signal)

### SYS-PWR-007 — Battery voltage amplitude analysis

The tool SHALL report for the match window:
- Minimum voltage
- Maximum voltage
- Mean voltage
- Voltage drop from pre-match idle (max before auto start) to minimum during match
- Number of brownout events (from `/SystemStats/BrownedOut` transitions)
- Total brownout duration (seconds)

### SYS-PWR-008 — Plot generation

The tool SHALL generate the following plots for each match processed:

1. **Battery voltage** vs elapsed time — with brownout threshold line (6.0V) and shaded brownout regions
2. **Current by subsystem** — stacked area chart, one colored band per subsystem group
3. **Total current** vs elapsed time
4. **Subsystem energy rank** — horizontal bar chart ordered by Wh, labeled with percentage

All time-series plots (1–3) SHALL include four vertical annotation lines:
- Auto start (t = 0)
- Teleop start
- Endgame start (MatchTime ≤ 30s)
- Match end

All plots SHALL display the session label in the title.

Plots SHALL be saved as PNG files to `--output-dir` (default: `./reports/`).

The tool SHALL work headlessly on Linux (no display required) by using the `Agg` matplotlib backend when no display is detected.

### SYS-PWR-009 — CLI summary report

The tool SHALL print a formatted summary table to stdout for each match:

```
Session: elimination-4
─────────────────────────────────────────────────────
Subsystem     │ Peak Current (A) │ Energy (Wh) │ % Total
─────────────────────────────────────────────────────
drive         │           87.3   │       34.2  │   58%
shooter       │           35.1   │       14.7  │   25%
...
─────────────────────────────────────────────────────
TOTAL         │          134.8   │       58.9  │  100%
─────────────────────────────────────────────────────
Battery voltage: min 10.8V  max 12.8V  drop 2.0V
Brownouts: 0 events
Note: unmeasured loads (radio, VRM, lights) excluded.
```

### SYS-PWR-010 (future) — Battery charge time prediction

When charging data is available, the tool SHALL estimate time to full charge given current state of charge and charge current.

**Status: DEFERRED** — requires discharge + charge curve data not yet collected.

---

## Non-Functional Requirements

### NFR-PERF-001 — Processing speed

The tool SHOULD process a single match log (≤ 60,000 rows, 325 columns) in under 30 seconds on a modern laptop.

### NFR-COMPAT-001 — Platform support

The tool SHALL run on Linux (Ubuntu 20.04+) and Windows (10/11) with Python 3.10+.

### NFR-COMPAT-002 — Python version

Requires Python ≥ 3.10 (already set in `pyproject.toml`).

### NFR-MAINT-001 — Configurable constants

Brownout threshold, endgame boundary, and subsystem signal mappings SHALL be defined in `config.py`, not scattered through analysis code.

---

## Constraints and Assumptions

- `/PowerDistribution/*` signals are always zero (old PDH, no CAN bus). Do not use.
- `/SystemStats/BatteryCurrent` is roboRIO input current (~0.4A), not main battery current.
- AKit CSV files are sparse — forward-fill must be applied before any analysis.
- MatchTime uses a **countdown** timer per period (not an elapsed clock).
- The gap between auto end and teleop start is typically 4–5 seconds; the robot is disabled during this gap.

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-02 | Initial version — requirements derived from championship log analysis and team goals |
