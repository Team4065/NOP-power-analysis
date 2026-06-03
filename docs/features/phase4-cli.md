# Feature: Phase 4 — CLI (cli.py)

---

## Status block

| Field | Value |
|---|---|
| Status | done (pending commit) |
| Owner | Team 4065 |
| Branch | main |
| Started | 2026-06-02 |

---

## Section 0 — Session state

| Field | Value |
|---|---|
| Current stage | 5 (implementation + tests green, verified on full-size real data) |
| Last worked | 2026-06-02 |
| Next action | Commit + push. Phase 5 (battery charge model) deferred until charge data exists. |
| Blocked on | — |
| Open PRs | — |

---

## Section 1 — Summary

Wire the full pipeline into a runnable command: `frc-power --log-dir <dir>`
discovers/converts logs, filters by session, prints a ranked summary table, and
saves the four analysis plots per match.

---

## Section 3 — System requirements

- SYS-PWR-001: Log directory ingestion (--log-dir)
- SYS-PWR-002: wpilog conversion (invokes AKitIngester.convert_all)
- SYS-PWR-003: Session filtering (--match-type, --match-number)
- SYS-PWR-008: Plot saving with session-labeled filenames
- SYS-PWR-009: CLI summary report table

---

## Section 4 — Key design decisions

- **`main(argv=None) -> int`** accepts an argv list for testability and returns an
  exit code (0 success, 1 nothing analyzed / no matches, 2 bad --log-dir). The
  console_scripts entry point calls `sys.exit(main())`.
- **Lazy matplotlib import**: `save_plots` imports the plots module only when plots
  are requested, so `--no-plots` runs without importing matplotlib.
- **Best-effort wpilog conversion**: if robotpy-wpiutil is missing, the CLI warns and
  continues with already-converted CSVs rather than aborting.
- **Pure formatting helper**: `format_summary_table` returns a string (no printing) so
  it is unit-testable without capturing stdout.
- Plots saved as `<session_label>_<plot_name>.png`; figures closed after save to
  bound memory across many matches.

---

## Section 5 — Files changed

| File | Action |
|---|---|
| `src/power_analysis/cli.py` | Implemented (was NotImplementedError stub) |
| `src/power_analysis/analysis/power_model.py` | Added `subsystem_peak_current()` |
| `tests/test_cli.py` | Created — 17 tests |
| `README.md` | Updated usage, features, docs table |

CLI surface:
```
frc-power --log-dir <dir> [--match-type all|practice|qual|elim]
          [--match-number N] [--output-dir ./reports] [--no-plots]
```

---

## Section 10 — Done checklist

- [x] Requirements covered (SYS-PWR-001/002/003/008/009)
- [x] Tests written (17)
- [x] Tests passing — full suite 101 tests green
- [x] ruff clean
- [x] Verified on full-size real data (cmptx_e4, 325MB / 55k rows)
- [ ] Committed and pushed

---

## Verified — full cmptx_e4 match (not the slice)

Ran `frc-power` against the real 325MB elimination-4 CSV in **3.9s** (NFR target 30s):

```
drive   82.1% (88.0 Wh, peak 656A)   shooter 15.7% (16.8 Wh)
hopper   1.8%                        climber  0.4%   intake 0.0%
TOTAL   107.2 Wh, peak 692A
Voltage: min 7.21V max 13.76V drop 6.55V
Brownouts: 1 event (0.02s)   ← the full match hit a brownout the 8.5s slice did not
```

All four period lines (match start / teleop / endgame / match end) render correctly
on the full-match voltage plot.
