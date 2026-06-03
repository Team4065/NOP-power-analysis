# Feature: Phase 3 — Visualization (plots.py)

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
| Current stage | 5 (implementation + tests green, visually verified) |
| Last worked | 2026-06-02 |
| Next action | Commit + push; then Phase 4 (CLI wiring) |
| Blocked on | — |
| Open PRs | — |

---

## Section 1 — Summary

Implement the four match-power plots, each annotated with match-period vertical
lines, operating on the normalized AKit DataFrame.

---

## Section 3 — System requirements

- SYS-PWR-007: Battery voltage amplitude (voltage plot with brownout line)
- SYS-PWR-008: Plot generation with match-period vertical lines

---

## Section 4 — Key design decisions

- **`match_periods(df)`** returns a `MatchPeriods` NamedTuple (match_start,
  teleop_start, endgame_start, match_end). Boundaries that don't occur in the
  captured data are `None` — e.g. the auto-only e4 slice has no teleop/endgame.
- **`add_period_lines(ax, periods)`** draws only the non-None boundaries, so plots
  degrade gracefully on partial captures (2 lines for auto-only, 4 for full match).
- **Headless backend**: plots.py selects the Agg backend before importing pyplot
  when on Linux with no DISPLAY. `tests/conftest.py` forces Agg unconditionally so
  the suite runs headlessly everywhere.
- **Idle-current clamp in stacked area only**: `plot_current_by_subsystem` clamps
  negative idle-sensor readings to 0 (`clip(lower=0)`) so the stack reads cleanly.
  The underlying data and energy math are left untouched (the Phase 2 open question
  about clamping in analysis remains open).
- Functions take a `session_label` that appears in every title.

---

## Section 5 — Files changed

| File | Action |
|---|---|
| `src/power_analysis/visualization/plots.py` | Rewritten — 4 plots + period helpers |
| `tests/conftest.py` | Created — Agg backend + akit_match_df session fixture |
| `tests/test_plots.py` | Created — 16 tests |

Plot functions:
- `plot_voltage(df, session_label)` — voltage line, brownout threshold, brownout
  shading, period lines
- `plot_total_current(df, session_label)` — total current with fill, period lines
- `plot_current_by_subsystem(df, session_label)` — stacked area per subsystem,
  period lines
- `plot_energy_rank(breakdown, session_label)` — horizontal bar chart, ranked
  descending, mWh + % labels

Note: the old stub functions `plot_current`, `plot_power`, `plot_channel_breakdown`
were replaced. `plot_channel_breakdown` (per-PDH-channel) is gone — PDH data is
always zero on this robot.

---

## Section 10 — Done checklist

- [x] Requirements covered (SYS-PWR-007/008)
- [x] Tests written (16)
- [x] Tests passing — full suite 84 tests green (Python 3.9 local)
- [x] ruff clean
- [x] Visually verified — all 4 PNGs rendered from real cmptx_e4 data
- [ ] Committed and pushed

---

## Verified output (cmptx_e4 slice)

All four plots rendered to PNG and visually inspected:
- **voltage.png** — sag to ~8.8V clearly visible; brownout line at 6.0V; start/end lines
- **total_current.png** — peaks near 500A during sprints
- **current_by_subsystem.png** — drive (blue) dominant, shooter (orange) ~32A baseline
- **energy_rank.png** — drive 79.9% (3259 mWh), shooter 20.2% (824 mWh), rest ~0
