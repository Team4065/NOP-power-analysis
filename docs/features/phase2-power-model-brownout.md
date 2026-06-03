# Feature: Phase 2 — PowerModel extension and BrownoutDetector

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
| Current stage | 5 (implementation + tests green) |
| Last worked | 2026-06-02 |
| Next action | Commit + push; then Phase 3 (plots.py) |
| Blocked on | — |
| Open PRs | — |

---

## Section 1 — Summary

Extend `PowerModel` to auto-detect AKit vs legacy schema and add subsystem energy
breakdown, energy ranking, and voltage statistics. Implement `BrownoutDetector` using
the `/SystemStats/BrownedOut` signal with a voltage-threshold fallback.

---

## Section 3 — System requirements

- SYS-PWR-005: Total power and energy computation
- SYS-PWR-006: Subsystem energy ranking
- SYS-PWR-007: Battery voltage amplitude analysis + brownout detection

---

## Section 4 — Key design decisions

- **Schema auto-detection**: `PowerModel.__init__` checks for `voltage_12v` column.
  Present → AKit mode (time from `elapsed_s` column). Absent → legacy mode (time
  from timestamp index). One class serves both; existing legacy tests unchanged.
- **Subsystem energy = ∫(V × subsystem_current) dt**. Because per-subsystem currents
  sum to `current_total` and V is a common factor, subsystem energies sum exactly to
  total energy (satisfies the ≤ invariant as equality).
- **VoltageStats** is a NamedTuple (min_v, max_v, mean_v, drop_v). `drop_v = max−min`;
  the in-window max approximates pre-match idle since the parser drops pre-match rows.
- **BrownoutDetector** prefers the `browned_out` boolean column; falls back to
  `voltage < threshold` (default 6.0V) when the signal column is absent. Contiguous
  runs are grouped with the `(mask != mask.shift()).cumsum()` idiom.

---

## Section 5 — Files changed

| File | Action |
|---|---|
| `src/power_analysis/analysis/power_model.py` | Extended — schema detect, breakdown, rank, voltage_stats, VoltageStats |
| `src/power_analysis/analysis/brownout_detector.py` | Implemented — signal + threshold paths |
| `tests/test_akit_power_model.py` | Created — 19 tests |
| `tests/test_brownout_detector.py` | Created — 13 tests |

---

## Section 8 — Risks / open questions

- **Idle-motor negative current**: idle motor current sensors read slightly negative
  (~−0.1 to −0.4 A). Integrated over a window, idle subsystems show tiny negative
  energy (e.g. climber at −0.1% on the e4 slice). This is sensor offset, not real
  regeneration. **Open decision for a later phase**: clamp negative currents to 0,
  or retain as-is for fidelity. Currently retained as-is. Magnitude is negligible.

---

## Section 10 — Done checklist

- [x] Requirements covered (SYS-PWR-005/006/007)
- [x] Tests written
- [x] Tests passing (68 AKit-suite tests green on Python 3.9 local; CI runs 3.10/3.11)
- [x] Legacy PowerModel behavior verified preserved (4 scenarios)
- [x] ruff clean on src/ and tests/
- [ ] Committed and pushed

---

## Verified results (cmptx_e4 slice, first 8.5s of match)

```
Total energy: 4079.5 mWh    Peak power: 5303 W    Avg power: 1740 W
Voltage: min=8.77V max=13.27V mean=10.81V drop=4.50V
Energy rank:  drive 79.9%  |  shooter 20.2%  |  hopper/intake ~0%  |  climber −0.1%
Brownouts: 0 events
```
