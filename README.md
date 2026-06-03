# FRC 4065 Power Analysis Tool

Telemetry-based power analysis platform built from Team 4065's
2026 World Championship robot data.

## Features

- AdvantageKit log ingestion — reads `.wpilog` and `.csv`, auto-converts unpaired wpilog files
- Single-match power analysis with automatic match-window extraction
- Total power and energy from the 12V main battery (Wh)
- Per-subsystem current and energy breakdown, ranked by consumption
- Battery voltage amplitude analysis and brownout detection
- Match-annotated plots (auto / teleop / endgame / match-end vertical lines)
- Session labeling (practice / qualification / elimination)
- Cross-platform (Linux + Windows)

---

## Installation

### 1. Clone the repo

```
git clone https://github.com/Team4065/NOP-power-analysis.git
cd NOP-power-analysis
```

### 2. Create a virtual environment

```
python -m venv venv
```

### 3. Activate

Windows:
```
venv\Scripts\activate
```

Linux / macOS:
```
source venv/bin/activate
```

### 4. Install dependencies

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

---

## Command-Line Usage

Point the tool at a directory of AdvantageKit logs. It discovers every log
(converting any unpaired `.wpilog` to `.csv`), analyzes each match, prints a
ranked summary, and saves plots.

```
frc-power --log-dir /path/to/championship_logs
```

Or without editable install:

```
python -m power_analysis.cli --log-dir /path/to/championship_logs
```

### Options

| Flag | Description |
|------|-------------|
| `--log-dir`, `-l` | **Required.** Directory of `.wpilog` / `.csv` logs. |
| `--match-type`, `-t` | Filter sessions: `all` (default), `practice`, `qual`, `elim`. |
| `--match-number`, `-n` | Filter to a specific match number. |
| `--output-dir`, `-o` | Where to save plot PNGs (default: `./reports`). |
| `--no-plots` | Print summaries only; skip plot generation. |

### Example output

```
Session: elimination-4
────────────────────────────────────────────────────────
Subsystem    │  Peak (A) │ Energy (Wh) │ % Total
────────────────────────────────────────────────────────
drive        │     655.8 │      88.031 │   82.1%
shooter      │     130.7 │      16.801 │   15.7%
hopper       │     140.2 │       1.931 │    1.8%
climber      │      87.9 │       0.414 │    0.4%
intake       │       0.0 │       0.000 │    0.0%
────────────────────────────────────────────────────────
TOTAL        │     692.0 │     107.177 │  100.0%
────────────────────────────────────────────────────────
Battery voltage: min 7.21V  max 13.76V  mean 10.44V  drop 6.55V
Brownouts: 1 event(s), 0.02s total
```

Each match produces four PNGs in the output directory:
`<session>_voltage.png`, `<session>_total_current.png`,
`<session>_current_by_subsystem.png`, `<session>_energy_rank.png`.

---

## Data Organisation

```
data/
├── sample/                  # Synthetic development data (committed)
└── seasons/
    ├── 2026/
    │   ├── raw/             # Real match logs — NOT committed (git-ignored)
    │   └── processed/       # Pipeline outputs — committed
    └── 2027/
        ├── raw/
        └── processed/
```

See [data/README.md](data/README.md) for full details and
[docs/telemetry_schema.md](docs/telemetry_schema.md) for the CSV column reference.

---

## Testing

```
pytest
```

Requires Python 3.10+. The suite covers the AdvantageKit ingester, parser,
power model, brownout detector, plots, and CLI, plus property-based numerical
invariants.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md) | What the tool must do (SYS-PWR IDs) |
| [docs/telemetry_schema.md](docs/telemetry_schema.md) | AdvantageKit signal reference |
| [docs/architecture.md](docs/architecture.md) | Module structure and design decisions |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | FRC / AKit term definitions |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy and invariants |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide for student contributors |

---

## Team

FRC Team 4065 — 2026 World Champions
