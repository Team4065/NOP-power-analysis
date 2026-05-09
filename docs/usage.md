# Usage Guide

## Installation

```bash
git clone https://github.com/Team4065/NOP-power-analysis.git
cd NOP-power-analysis
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

---

## Command-Line Interface

Analyze a single telemetry file and print a summary report:

```bash
frc-power --input data/sample/2026_sample_match_1.csv --report
```

Or using the module directly (no install required):

```bash
python -m power_analysis.cli --input data/sample/2026_sample_match_1.csv --report
```

### Options

| Flag | Description |
|------|-------------|
| `--input`, `-i` | Path to telemetry CSV (required) |
| `--season`, `-s` | Competition season year (default: 2026) |
| `--report` | Print a summary power report to stdout |

---

## Streamlit Dashboard

Launch the interactive visualizer:

```bash
streamlit run src/power_analysis/visualization/dashboard.py
```

Open http://localhost:8501 in your browser. Use the sidebar to upload a CSV
or select a sample file, then explore the power metrics and charts.

---

## Python API

```python
from power_analysis.parsers.telemetry_parser import TelemetryParser
from power_analysis.analysis.power_model import PowerModel
from power_analysis.analysis.battery_model import BatteryModel
from power_analysis.analysis.brownout_detector import BrownoutDetector

# 1. Load data
df = TelemetryParser("data/sample/2026_sample_match_1.csv").load()

# 2. Power metrics
model = PowerModel(df)
print(f"Peak power:    {model.peak_power():.1f} W")
print(f"Average power: {model.average_power():.1f} W")
print(f"Total energy:  {model.compute_energy():.3f} Wh")

# 3. Battery health
batt = BatteryModel(df)
print(f"R_internal: {batt.estimate_internal_resistance():.4f} Ω")

# 4. Brownout events
detector = BrownoutDetector(df)
events = detector.detect()
print(f"{detector.brownout_count()} brownout event(s) detected")
print(events)
```

---

## Testing

```bash
pytest              # run all tests
pytest -v           # verbose output
pytest tests/test_power_model.py   # single file
```

Tests for unimplemented functions will raise `NotImplementedError`.
A passing test confirms a correct implementation.

---

## Adding Real Match Data

1. Export your match log from WPILib DataLog Tool or AdvantageScope as CSV.
2. Verify column names match [telemetry_schema.md](telemetry_schema.md).
3. Place the file in `data/seasons/<year>/raw/` — it will not be committed to git.
4. Pass the path to `TelemetryParser` or the CLI `--input` flag.
