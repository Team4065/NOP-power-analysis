# Feature: Phase 1 — AKit Ingester and Parser

---

## Status block

| Field | Value |
|---|---|
| Status | in-progress |
| Owner | Team 4065 |
| Branch | main |
| Started | 2026-06-02 |

---

## Section 0 — Session state

| Field | Value |
|---|---|
| Current stage | 4 (implementation complete, tests written, awaiting test run) |
| Last worked | 2026-06-02 |
| Next action | Set up Python venv, run pytest, verify green; then commit |
| Blocked on | No pytest environment currently configured on dev machine |
| Open PRs | — |

---

## Section 1 — Summary

Implement `AKitIngester` (file discovery, wpilog→csv, session labeling) and `AKitParser` (AKit CSV → normalized match DataFrame) to replace the old flat-schema `TelemetryParser` as the primary data ingestion path.

---

## Section 2 — Motivation

The real FRC 2026 championship logs use AdvantageKit format (sparse CSV with `/`-prefixed signal paths), which is completely different from the synthetic flat-schema the project originally assumed. Without this layer, no real data can be analyzed. This phase is the prerequisite for all downstream power analysis and plotting work.

---

## Section 3 — System requirements

- SYS-PWR-001: Log directory ingestion
- SYS-PWR-002: Automatic wpilog → CSV conversion
- SYS-PWR-003: Session type detection and labeling
- SYS-PWR-004: Match window extraction and elapsed-time axis
- SYS-PWR-005: Total current derivation (motor sum)
- SYS-PWR-006: Per-subsystem current grouping
- SYS-PWR-007: Battery voltage column (voltage_12v)

---

## Section 4 — Key design decisions

- `AKitIngester` is format-agnostic at discovery time; `is_akit_format()` peeks at CSV headers
- wpilog conversion delegated to `_wpilog_convert.py` (internal module, requires `robotpy-wpiutil`)
- `AKitParser.load()` always forward-fills before any processing — AKit sparse semantics
- Match window = Enabled=True AND MatchTime > 0 (excludes pre-match staging and post-match)
- elapsed_s starts at 0.0 from the first auto-enabled row; makes plots comparable across matches
- PDH channels are always 0 on this robot — not referenced anywhere in the parser
- Subsystem groupings defined in `config.AKIT_MOTOR_CURRENT_COLS` — parser has no hardcoded signal names
- Legacy `TelemetryParser` preserved; existing tests unchanged

---

## Section 5 — Files changed

| File | Action |
|---|---|
| `src/power_analysis/parsers/akit_ingester.py` | Created |
| `src/power_analysis/parsers/akit_parser.py` | Created |
| `src/power_analysis/parsers/_wpilog_convert.py` | Created (private) |
| `src/power_analysis/__init__.py` | Updated — exports AKitIngester, AKitParser, LogFile |
| `tests/test_akit_ingester.py` | Created |
| `tests/test_akit_parser.py` | Created |
| `tests/fixtures/akit_e4_slice.csv` | Created — 400-row real match data slice |

---

## Section 10 — Done checklist

- [x] SRD entries defined (via SYSTEM_REQUIREMENTS.md)
- [x] Tests written
- [ ] Tests passing (green) — needs pytest environment
- [ ] Coverage ≥ 85%
- [ ] Committed and pushed
