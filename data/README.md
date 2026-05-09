# Data Directory

## Layout

```
data/
├── sample/          # Synthetic match data for development and testing
│   ├── 2026_sample_match_1.csv
│   └── 2026_sample_match_2.csv
│
└── seasons/
    ├── 2026/
    │   ├── raw/       # Raw competition telemetry logs — NOT committed to git
    │   └── processed/ # Cleaned outputs from the analysis pipeline
    └── 2027/
        ├── raw/
        └── processed/
```

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
