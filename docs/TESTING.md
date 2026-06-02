# Testing Strategy

FRC Team 4065 Power Analysis Tool — test approach and invariants.

---

## Philosophy

- Tests are the executable specification. Write them before the implementation.
- A silent wrong answer (energy computed with wrong sign, wrong time bounds) is worse than a crash. Numerical invariants must be enforced.
- Use real data for integration tests. The synthetic 30-row CSVs verify the old flat-schema parser; real championship data (a committed fixture slice) verifies the AKit pipeline.

---

## Test Pyramid

| Layer | Share | Scope |
|---|---|---|
| Unit | ~55% | Parser arithmetic, model math, signal mapping |
| Integration | ~35% | Full pipeline from CSV fixture → model output |
| Property | ~10% | Numerical invariants via `hypothesis` |

No E2E / Streamlit tests in Phase 1.

---

## Stack

| Tool | Role |
|---|---|
| `pytest` | Test runner |
| `hypothesis` | Property-based tests for numerical invariants |
| `coverage.py` | Line + branch coverage |
| `pytest-cov` | Coverage integration |

---

## Directory Layout

```
tests/
├── conftest.py                  # shared fixtures
├── fixtures/
│   ├── akit_e4_slice.csv        # real championship data slice (power columns only, ~300 rows)
│   └── (existing synthetic CSVs stay for TelemetryParser tests)
├── test_akit_ingester.py        # wpilog discovery, format detection, session labeling
├── test_akit_parser.py          # forward-fill, match window extraction, current derivation
├── test_power_model.py          # energy, peak, average, subsystem breakdown (existing + extended)
├── test_brownout_detector.py    # brownout detection via BrownedOut signal
├── test_plots.py                # plot functions return Figure objects; period lines present
├── test_parser.py               # existing TelemetryParser tests (keep, don't break)
├── test_power_model_legacy.py   # existing PowerModel tests against synthetic data
└── test_sample_data.py          # existing sample data validation (keep)
```

---

## Key Fixtures (`conftest.py`)

```python
@pytest.fixture(scope="session")
def akit_match_df():
    """Parsed, normalized DataFrame for one real match window (cmptx_e4 slice)."""

@pytest.fixture
def minimal_match_df():
    """Tiny synthetic AKit-format DataFrame for fast unit tests."""
```

---

## Naming Convention

`test_<behavior>_<condition>_<expected_result>`

Examples:
- `test_akit_parser_load_returns_normalized_columns`
- `test_power_model_energy_is_positive_for_any_valid_match`
- `test_brownout_detector_uses_browned_out_signal_not_threshold`

---

## Property-Based Test Invariants (`hypothesis`)

These must hold for any valid match window:

1. **Energy ≥ 0**: `compute_energy(df) >= 0` for all non-negative voltage and current inputs
2. **Peak ≥ average**: `peak_power(df) >= average_power(df)`
3. **Voltage in range**: all values of `voltage_12v` in `[0.0, 15.0]` after parsing
4. **Subsystem sum ≤ total**: sum of subsystem Wh ≤ total Wh (some loads unmeasured)
5. **Current sum is total**: `current_total == sum(all motor currents)` row-wise within float tolerance
6. **Elapsed time monotonic**: `elapsed_s` index is strictly increasing

---

## Test Writing Loop

1. Find the relevant requirement ID in `docs/SYSTEM_REQUIREMENTS.md`
2. Write the test referencing it in the docstring: `"""SYS-PWR-005: ..."""`
3. Run pytest — confirm the test fails (red)
4. Implement the minimum code to make it pass (green)
5. Run full test file — confirm no regressions
6. Refactor if needed, keeping tests green

---

## Coverage Targets

- Line coverage: ≥ 85% on `src/` (goal: 90%+)
- Branch coverage: enabled
- Exclude: `raise NotImplementedError` stubs, `if TYPE_CHECKING`, abstract methods

Run coverage:
```
pytest --cov=power_analysis --cov-report=term-missing tests/
```

---

## Database / External State

This tool has no database. The only external state is the filesystem (log files). Tests use committed fixture files — no network, no external services.
