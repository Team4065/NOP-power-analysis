# Data Directory

## Layout

```
data/
├── sample/          # Sample data for development, testing, and tool review
│   ├── akit_cmptx_e4_sample.wpilog   # real elimination match (trimmed) — see below
│   ├── akit_cmptx_e4_sample.csv      # the same match, converted by this tool
│   ├── 2026_sample_match_1.csv       # legacy synthetic flat-schema data
│   └── 2026_sample_match_2.csv       # legacy synthetic flat-schema data
│
└── seasons/
    ├── 2026/
    │   ├── raw/       # Raw competition telemetry logs — NOT committed to git
    │   └── processed/ # Cleaned outputs from the analysis pipeline
    └── 2027/
        ├── raw/
        └── processed/
```

## Sample AdvantageKit match (for reviewers / students)

`akit_cmptx_e4_sample.{wpilog,csv}` is a **real** 2026 World Championship
elimination match (Elimination 4), provided so peers and students can run the
tool end-to-end without needing the multi-hundred-MB raw logs.

To keep it committable to plain git, it was trimmed to:
- the match window only (auto → match end, with a short pre/post buffer), and
- only the ~25 power-relevant signals the tool analyzes.

It still reproduces the full match exactly: drive 82.1%, shooter 15.7%,
total 107 Wh, a real brownout, and a voltage sag to 7.21 V.

Try it both ways:

```
# Pre-converted CSV is already present — analyze directly:
frc-power --log-dir data/sample

# Or delete the CSV and let the tool convert the wpilog for you:
rm data/sample/akit_cmptx_e4_sample.csv
frc-power --log-dir data/sample
```

The sample was generated with [`scripts/make_sample.py`](../scripts/make_sample.py)
(documented there for reproducibility). The legacy `2026_sample_match_*.csv` files
use the older synthetic flat schema and exist only to exercise the legacy
`TelemetryParser`.

## Telemetry Schema

See [../docs/telemetry_schema.md](../docs/telemetry_schema.md) for full column definitions.

## Raw Data Policy

Raw competition logs can be large (several MB per match) and may contain
sensitive timing information. They are excluded from version control via `.gitignore`.

To add your own match data:
1. Export your match log from WPILib DataLog Tool or AdvantageScope as CSV.
2. Ensure column names match [../docs/telemetry_schema.md](../docs/telemetry_schema.md).
3. Place the file in `data/seasons/<year>/raw/`.

## Processed Data

Processed outputs (summary CSVs, power reports) are committed and stored in
`data/seasons/<year>/processed/`.
