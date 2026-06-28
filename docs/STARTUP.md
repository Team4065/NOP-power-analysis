# Startup on a New Compute Asset

This guide gets the project running from scratch on a fresh machine and — just as
important — lists what lives **outside** the git repo and must be transferred
separately so nothing is lost in the move.

---

## 1. What `git clone` gives you (everything tracked)

```
git clone https://github.com/Team4065/NOP-power-analysis.git
cd NOP-power-analysis
```

A clean clone is fully self-sufficient for development and tool review. It
includes:

- All source (`src/power_analysis/`), tests (`tests/`), and docs (`docs/`).
- Dependency manifests: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`.
- **A real competition sample** — `data/sample/akit_cmptx_e4_sample.{wpilog,csv}`,
  a trimmed-but-real 2026 World Championship Elimination 4 match. It reproduces
  the full match (drive 82.1%, shooter 15.7%, 107 Wh, a real brownout, 7.21 V
  sag) and lets a new machine run the tool end-to-end with no external data.
- Example report PNGs in `reports/` (the four `elimination-4_*` plots).

You do **not** need anything else to verify the tool works. See step 4.

---

## 2. Environment setup

Python **3.10+** is required (the codebase uses 3.10 syntax; CI runs 3.10 and 3.11
on Linux and Windows).

> Note: this project was last developed against system Python 3.9 with
> `PYTHONPATH=src` and no virtualenv, which runs the CLI but **cannot** run the
> full test suite (the tests need 3.10+). On the new machine, install 3.10+ so
> tests pass.

```bash
python -m venv venv

# Activate — Windows:
venv\Scripts\activate
# Activate — Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

`pip install -e .` installs the `frc-power` console command. Without it, invoke
the CLI as `PYTHONPATH=src python -m power_analysis.cli ...`.

Dependencies are intentionally **unpinned** (CI validates against current
releases). If you need byte-for-byte reproducibility, run
`pip freeze > requirements.lock` on a known-good machine and carry that file.

---

## 3. ⚠️ Data that is NOT in git — transfer it separately

| What | Location | In git? | Action before abandoning this machine |
|------|----------|---------|----------------------------------------|
| **Raw championship logs** | `../championship_logs/` (sibling dir, **~1.8 GB, 42 files**) | **NO** — git-ignored, too large | **Back up to cloud / external drive.** Exists nowhere else. |
| Real match logs you add | `data/seasons/<year>/raw/` | NO — git-ignored | Back up if you want to keep them |
| Generated reports | `reports/` (except the 4 committed examples) | NO | Regenerable from logs; optional |

The committed sample (step 1) covers tool review and demos. The full
`championship_logs` set is only needed to:

- regenerate or re-trim the committed sample (`scripts/make_sample.py`), or
- run the tool across the entire championship dataset.

If you do not back it up, the raw 2026 World Championship telemetry is **lost**.

After moving the logs to the new machine, point the tool at them:

```bash
frc-power --log-dir ../championship_logs
```

(The tool takes `--log-dir` at runtime; no path is hardcoded, so the logs can
live anywhere.)

---

## 4. Verify the new machine works

Run the committed sample — no external data needed:

```bash
frc-power --log-dir data/sample --no-plots
```

Expected: a `Session: elimination-4` summary with drive 82.1%, total 107.177 Wh,
1 brownout event.

Then run the test suite (requires 3.10+):

```bash
pytest
```

---

## 5. Migration checklist

- [ ] Clone is pushed and `origin/main` is up to date (`git status` clean, `git push`).
- [ ] **`../championship_logs/` (1.8 GB) backed up to durable storage.**
- [ ] Any local `data/seasons/*/raw/` logs backed up if worth keeping.
- [ ] New machine has Python 3.10+.
- [ ] `frc-power --log-dir data/sample --no-plots` produces the expected summary.
- [ ] `pytest` passes.
