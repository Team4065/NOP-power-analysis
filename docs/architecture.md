# Architecture

## Data Flow

```
User supplies: --log-dir /path/to/logs/
                    │
                    ▼
         AKitIngester  (parsers/akit_ingester.py)
          ├── Discover .wpilog and .csv files
          ├── Convert .wpilog → .csv  (robotpy-wpiutil, if no paired CSV)
          ├── Auto-detect AKit vs legacy flat-schema
          └── Return list of LogFile(path, session_label, match_type, match_number)
                    │
                    ▼ (one LogFile at a time)
         AKitParser  (parsers/akit_parser.py)
          ├── Read sparse CSV; forward-fill nulls
          ├── Parse bool strings ("True"/"False")
          ├── Detect match window (Enabled=True, MatchTime > 0)
          ├── Build elapsed_s index from auto start
          ├── Derive current_total = Σ motor currents
          └── Return normalized DataFrame
                    │
         ┌──────────┴────────────────────┐
         ▼                               ▼
   PowerModel                    BrownoutDetector
   (analysis/power_model.py)     (analysis/brownout_detector.py)
    ├── compute_instantaneous_power()   detect() via /SystemStats/BrownedOut
    ├── compute_energy()                brownout_count()
    ├── peak_power()                    total_brownout_duration()
    ├── average_power()
    ├── subsystem_energy_breakdown()
    ├── rank_by_energy()
    └── voltage_stats()
         │
         └──────────────────────────────┐
                                        ▼
                               plots.py  (visualization/plots.py)
                                ├── plot_voltage()
                                ├── plot_current_by_subsystem()
                                ├── plot_total_current()
                                └── plot_energy_rank()
                                        │
                               cli.py ──┘
                                ├── Summary table to stdout
                                └── PNG files to --output-dir

All modules
  └── config.py    (AKit signal paths, subsystem groupings, thresholds)
  └── utils/logger.py
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `parsers/akit_ingester.py` | File discovery, wpilog→csv conversion, format detection, session labeling |
| `parsers/akit_parser.py` | AKit CSV → normalized match DataFrame |
| `parsers/telemetry_parser.py` | Legacy flat-schema parser (kept for synthetic test data) |
| `analysis/power_model.py` | All power and energy calculations, subsystem breakdown |
| `analysis/brownout_detector.py` | Brownout event detection and characterization |
| `analysis/battery_model.py` | Internal resistance estimation; charge time (deferred) |
| `visualization/plots.py` | Matplotlib figures — voltage, current, energy rank |
| `visualization/dashboard.py` | Streamlit web app (deferred) |
| `cli.py` | Entry point: argument parsing, orchestration, report printing |
| `config.py` | All constants: signal paths, subsystem groups, thresholds |
| `utils/logger.py` | Named logger factory |

## Key Design Decisions

### PDH data is unavailable
The 2026 robot uses an older PDH model with no CAN bus. All `/PowerDistribution/*`
signals are always zero. Total current is derived by summing all individual motor
current signals. This is noted in every output.

### Battery voltage source
`/SystemStats/BatteryVoltage` is the only reliable voltage signal. It is measured
by the roboRIO's analog input. `/SystemStats/BatteryCurrent` (~0.4A) is the
roboRIO's own supply current — not main battery current.

### Brownout via signal, not threshold
`/SystemStats/BrownedOut` is a boolean logged directly by WPILib when brownout
protection activates. This is used instead of applying a voltage threshold to
`BatteryVoltage`, because the threshold is configurable per-robot (Team 4065
uses 6.0V, not the WPILib default of 6.8V).

### Forward-fill before analysis
AKit CSV files are sparse — signals only appear in rows where they changed.
`AKitParser` applies `pd.DataFrame.ffill()` immediately after loading so all
downstream code works with a dense time series.

### Elapsed-time axis
The raw `Timestamp` column is robot clock from boot (hundreds of seconds into
a session). All analysis uses an `elapsed_s` axis starting at 0 from the first
auto-enabled row, making plots comparable across matches.

### Cross-platform file paths
All file operations use `pathlib.Path`. No string path separators. CLI argument
`--log-dir` is converted to `Path` at entry. Matplotlib uses `Agg` backend
on headless Linux (no display); on Windows and Linux with display, the default
backend is used.

### src/ layout
Prevents accidental import of the uninstalled package. `pip install -e .` is
required to run the tool.

### Legacy TelemetryParser preserved
The flat-schema `TelemetryParser` and its tests are kept intact. They serve
as test coverage for any team that exports telemetry in the older flat format.
The `AKitParser` is the primary production parser.
