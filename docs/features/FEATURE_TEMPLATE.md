# Feature: [Short Name]

<!-- Copy this file to docs/features/<kebab-slug>.md for each new feature -->

---

## Status block

| Field | Value |
|---|---|
| Status | draft / approved / in-progress / blocked / done |
| Owner | |
| Branch | |
| Started | |

---

## Section 0 — Session state (update every session)

| Field | Value |
|---|---|
| Current stage | 1 / 2 / 3 / 4 / 5 / 6 |
| Last worked | YYYY-MM-DD |
| Next action | |
| Blocked on | — |
| Open PRs | — |

---

## Section 1 — Summary

One sentence describing what this feature adds.

---

## Section 2 — Motivation

2–4 sentences: what problem does this solve, why now, what's the expected outcome.

---

## Section 3 — System requirements

List the `SYS-PWR-XXX` IDs from `docs/SYSTEM_REQUIREMENTS.md` that this feature implements. Flag if any new requirements need to be added.

- SYS-PWR-XXX: ...

---

## Section 4 — SRD entries (software requirements)

For each requirement, one entry:

**SRD-PWR-XXX** (Parent: SYS-PWR-YYY)
- **Given**: system state / precondition
- **When**: action taken
- **Then**: expected outcome
- **Acceptance**: measurable pass/fail criterion
- **Out of scope**: what this does NOT cover

---

## Section 5 — Test plan

For each SRD entry:

| SRD | Layer | Positive | Negative | Boundary |
|---|---|---|---|---|
| SRD-PWR-XXX | unit | ... | ... | ... |

Property tests to add (if any numerical invariants are involved):
- ...

---

## Section 6 — Affected modules

Files expected to change:
- `src/power_analysis/...`
- `tests/...`

---

## Section 7 — Out of scope

Explicit non-goals for this feature.

---

## Section 8 — Risks / open questions

- ...

---

## Section 9 — Adversarial review results

(Fill in after implementation — three independent review passes)

1. Test-only review: ...
2. Requirements-vs-tests review: ...
3. Implementation review: ...

---

## Section 10 — Done checklist

- [ ] SRD entries approved
- [ ] Test plan approved
- [ ] Tests written (red)
- [ ] Tests passing (green)
- [ ] Coverage ≥ 85% on changed files
- [ ] Adversarial review complete
- [ ] GLOSSARY.md updated if new terms introduced
- [ ] architecture.md updated if data flow changed
