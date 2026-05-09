# Architecture

## Module Dependency Diagram

```
cli.py
  └── TelemetryParser     (parsers/telemetry_parser.py)
  └── PowerModel          (analysis/power_model.py)
  └── BatteryModel        (analysis/battery_model.py)
  └── BrownoutDetector    (analysis/brownout_detector.py)

dashboard.py
  └── TelemetryParser
  └── PowerModel
  └── BatteryModel
  └── BrownoutDetector
  └── plots.py            (visualization/plots.py)

All modules
  └── config.py           (column names, thresholds, paths)
  └── utils/logger.py     (logging)
```

## Data Flow

```
CSV file on disk
    │
    ▼
TelemetryParser.load()
    │  returns pd.DataFrame indexed by timestamp
    ▼
┌─────────────────────┬────────────────────┬──────────────────────┐
│   PowerModel        │   BatteryModel     │   BrownoutDetector   │
│                     │                    │                      │
│ compute_power()     │ estimate_R()       │ detect()             │
│ compute_energy()    │ open_circuit_V()   │ brownout_count()     │
│ peak_power()        │                    │                      │
│ average_power()     │                    │                      │
└─────────────────────┴────────────────────┴──────────────────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                        plots.py / dashboard.py
```

## Design Decisions

### Why `src/` layout?
The `src/` layout prevents Python from accidentally importing the uninstalled
package from the working directory. Running `pip install -e .` is required;
this surfaces import issues early rather than in production.

### Why `raise NotImplementedError` instead of `pass`?
Stubs that `pass` silently return `None`. `NotImplementedError` causes every
downstream caller — including tests — to fail loudly, making it obvious what
still needs to be implemented.

### Why separate `config.py`?
Column names and thresholds are used across parsers, analysis modules, and tests.
Centralising them in `config.py` means a schema change requires editing one file,
not hunting through every module.

### Why trapezoidal integration for energy?
FRC telemetry is logged at approximately 50 Hz but the interval is not perfectly
uniform. `np.trapz(y, x)` handles variable timestep widths correctly, unlike a
simple sum that assumes a fixed dt.
