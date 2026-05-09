# FRC 4065 Power Analysis Tool

Telemetry-based power analysis platform built from Team 4065's
2026 World Championship robot data.

## Features

- Telemetry parsing from CSV match logs
- Electrical power calculation (instantaneous, peak, average)
- Total energy consumption per match (Wh)
- Subsystem current breakdown by PDH channel
- Brownout detection and characterisation
- Battery internal resistance modeling
- Interactive match power visualiser (Streamlit GUI)
- Multi-season support (2026 data + 2027 development)

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

Analyse a telemetry file and print a summary report:

```
frc-power --input data/sample/2026_sample_match_1.csv --report
```

Or without editable install:

```
python -m power_analysis.cli --input data/sample/2026_sample_match_1.csv --report
```

---

## Launch GUI Visualizer

```
streamlit run src/power_analysis/visualization/dashboard.py
```

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

Tests that fail with `NotImplementedError` indicate functions still awaiting
student implementation — that is by design. A passing test confirms a correct
implementation.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/telemetry_schema.md](docs/telemetry_schema.md) | CSV column definitions |
| [docs/architecture.md](docs/architecture.md) | Module structure and design decisions |
| [docs/usage.md](docs/usage.md) | CLI and API usage guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide for student contributors |

---

## Team

FRC Team 4065 — 2026 World Champions
