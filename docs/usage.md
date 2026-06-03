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

Point the tool at a directory of AdvantageKit logs. It discovers every log
(converting any unpaired `.wpilog` to `.csv`), analyzes each match, prints a
ranked summary, and saves plots.

```bash
frc-power --log-dir data/sample
```

Or using the module directly (no install required):

```bash
python -m power_analysis.cli --log-dir data/sample
```

### Options

| Flag | Description |
|------|-------------|
| `--log-dir`, `-l` | **Required.** Directory of `.wpilog` / `.csv` logs. |
| `--match-type`, `-t` | Filter sessions: `all` (default), `practice`, `qual`, `elim`. |
| `--match-number`, `-n` | Filter to a specific match number. |
| `--output-dir`, `-o` | Where to save plot PNGs (default: `./reports`). |
| `--no-plots` | Print summaries only; skip plot generation. |

The committed sample in `data/sample/` is a real elimination match — try it both
ways:

```bash
# Analyze the pre-converted CSV directly:
frc-power --log-dir data/sample

# Or delete the CSV and let the tool convert the wpilog for you:
rm data/sample/akit_cmptx_e4_sample.csv
frc-power --log-dir data/sample
```

---

## Python API

```python
from pathlib import Path

from power_analysis.parsers.akit_parser import AKitParser
from power_analysis.analysis.power_model import PowerModel
from power_analysis.analysis.brownout_detector import BrownoutDetector

# 1. Load and normalize one match
df = AKitParser(Path("data/sample/akit_cmptx_e4_sample.csv")).load()

# 2. Power metrics
model = PowerModel(df)
print(f"Peak power:    {model.peak_power():.1f} W")
print(f"Average power: {model.average_power():.1f} W")
print(f"Total energy:  {model.compute_energy():.3f} Wh")

# 3. Subsystem ranking
for name, wh in model.rank_by_energy():
    print(f"  {name:<10} {wh:.3f} Wh")

# 4. Voltage and brownouts
vs = model.voltage_stats()
print(f"Voltage: min {vs.min_v:.2f}V  max {vs.max_v:.2f}V  drop {vs.drop_v:.2f}V")
detector = BrownoutDetector(df)
print(f"{detector.brownout_count()} brownout event(s)")
```

For AdvantageKit log discovery and wpilog conversion, use `AKitIngester`:

```python
from power_analysis.parsers.akit_ingester import AKitIngester

ingester = AKitIngester(Path("data/sample"))
ingester.convert_all()            # wpilog -> csv for any unconverted files
for log in ingester.discover():   # list[LogFile]
    print(log.session_label, log.path)
```

---

## Testing

```bash
pytest              # run all tests
pytest -v           # verbose output
pytest tests/test_cli.py   # single file
```

---

## Adding Real Match Data

1. Copy your `.wpilog` files (and/or AdvantageScope-exported `.csv` files) into a
   directory.
2. Run `frc-power --log-dir <that directory>`. Unpaired `.wpilog` files are
   converted automatically.
3. Large raw logs belong in `data/seasons/<year>/raw/` — that path is git-ignored.
