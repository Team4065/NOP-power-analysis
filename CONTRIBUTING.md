# Contributing to FRC 4065 Power Analysis

Welcome! This project is developed by students on FRC Team 4065 with mentor guidance.

---

## Getting Started

### 1. Clone and set up your environment

```bash
git clone https://github.com/Team4065/NOP-power-analysis.git
cd NOP-power-analysis
python -m venv venv
```

**Windows:**
```
venv\Scripts\activate
```

**Linux / macOS:**
```
source venv/bin/activate
```

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

---

## Project Structure

```
src/power_analysis/     # All source code lives here
tests/                  # One test file per source module
docs/                   # Reference documentation
data/sample/            # Sample CSVs for development
notebooks/              # Jupyter exploration notebooks
```

---

## Where to Start Coding

Every module under `src/power_analysis/` has function stubs with `# TODO:` comments
and `raise NotImplementedError(...)`. Your job is to implement those functions.

**Recommended order:**
1. `parsers/telemetry_parser.py` — nothing else works until data loads
2. `analysis/power_model.py` — core power calculations
3. `analysis/battery_model.py` — battery resistance estimation
4. `analysis/brownout_detector.py` — event detection
5. `visualization/plots.py` — matplotlib charts
6. `visualization/dashboard.py` — Streamlit app
7. `cli.py` — wire it all together

---

## Running Tests

```bash
pytest
```

Tests will fail with `NotImplementedError` until you implement the corresponding function —
that is expected. A passing test means your implementation is correct.

To run a single file:
```bash
pytest tests/test_power_model.py -v
```

---

## Code Style

- Format code with **Black** before committing:
  ```bash
  black src/ tests/
  ```
- Lint with **Ruff**:
  ```bash
  ruff check src/ tests/
  ```

---

## Branching and Pull Requests

1. Create a branch for your feature or fix:
   ```bash
   git checkout -b your-name/feature-description
   ```
2. Make your changes and commit with a clear message.
3. Open a pull request on GitHub — a mentor will review it.

---

## Questions?

Ask a mentor or open a GitHub Issue describing what you are stuck on.
