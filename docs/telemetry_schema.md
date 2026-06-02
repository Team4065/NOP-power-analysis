# Telemetry Schema

Real championship log format for FRC Team 4065 (2026 season).

---

## File format

Logs are produced by **AdvantageKit** and stored as `.wpilog` (binary) with a paired `.csv` (text).

### wpilog

Binary WPILib DataLog format. Must be converted to CSV using `robotpy-wpiutil` before analysis.
Naming: `akit_<YY-MM-DD>_<HH-MM-SS>_<event>[_suffix].wpilog`

### AKit CSV

Sparse time series — each signal appears in a row **only when its value changed** since the last row. All other cells are `null` or empty. **Always apply forward-fill (`ffill`) before analysis.**

First column is always `Timestamp` (robot clock, seconds). Remaining columns are AKit signal paths with forward-slash separators.

Event suffixes:
- `_daly` — Daly division (practice/qualification rounds)
- `_cmptx` — Championship finals/playoffs
- `_e{N}` suffix on some cmptx files — elimination match number

---

## Signal reference

### Timestamp

| Column | Type | Unit | Notes |
|---|---|---|---|
| `Timestamp` | float | s | Robot clock from boot. Not match-relative. Derive elapsed time from match start. |

### Battery and power

| Signal path | Type | Unit | Status | Notes |
|---|---|---|---|---|
| `/SystemStats/BatteryVoltage` | float | V | **Use this** | 12V terminal voltage at roboRIO. Real data. |
| `/SystemStats/BrownedOut` | bool string | — | **Use this** | `"True"` when voltage drops below brownout threshold. |
| `/SystemStats/BrownoutVoltage` | float | V | Read at startup | Configured threshold = **6.0V** (not WPILib default 6.8V). |
| `/SystemStats/BatteryCurrent` | float | A | Do not use for total | roboRIO input current only (~0.4A). Not main battery current. |
| `/PowerDistribution/Voltage` | float | V | **Always 0** | Old PDH has no CAN bus. Ignore. |
| `/PowerDistribution/TotalCurrent` | float | A | **Always 0** | Same reason. Ignore. |
| `/PowerDistribution/TotalPower` | float | W | **Always 0** | Same. Ignore. |
| `/PowerDistribution/TotalEnergy` | float | J | **Always 0** | Same. Ignore. |
| `/PowerDistribution/ChannelCurrent` | float[] | A | **Always 0** | 24-element comma-separated array. All zeros. Ignore. |

### Driver Station / match state

| Signal path | Type | Notes |
|---|---|---|
| `/DriverStation/Enabled` | bool string | `"True"` / `"False"` — robot enabled flag |
| `/DriverStation/Autonomous` | bool string | `"True"` during auto period |
| `/DriverStation/MatchTime` | float | Countdown timer (s). ~20 at auto start, ~140 at teleop start, -1 outside match |
| `/DriverStation/MatchType` | int | 0=None, 1=Practice, 2=Qualification, 3=Elimination |
| `/DriverStation/MatchNumber` | int | Match number within type |
| `/DriverStation/DSAttached` | bool string | Driver station connected |

### Motor currents — Drive (swerve, 4 modules)

| Signal path | Type | Unit | Notes |
|---|---|---|---|
| `/Drive/Module0/DriveCurrentAmps` | float | A | Front-left drive motor |
| `/Drive/Module0/TurnCurrentAmps` | float | A | Front-left steer motor |
| `/Drive/Module1/DriveCurrentAmps` | float | A | Front-right drive motor |
| `/Drive/Module1/TurnCurrentAmps` | float | A | Front-right steer motor |
| `/Drive/Module2/DriveCurrentAmps` | float | A | Rear-left drive motor |
| `/Drive/Module2/TurnCurrentAmps` | float | A | Rear-left steer motor |
| `/Drive/Module3/DriveCurrentAmps` | float | A | Rear-right drive motor |
| `/Drive/Module3/TurnCurrentAmps` | float | A | Rear-right steer motor |

### Motor currents — Shooter

| Signal path | Type | Unit | Notes |
|---|---|---|---|
| `/Shooter/TopRollerMotorCurrentAmps` | float | A | Top flywheel roller |
| `/Shooter/BottomRollerMotorCurrentAmps` | float | A | Bottom flywheel roller |
| `/Shooter/AngleMotorCurrentAmps` | float | A | Shooter pivot angle |

### Motor currents — Hopper

| Signal path | Type | Unit | Notes |
|---|---|---|---|
| `/Hopper/AgitatorCurrentAmps` | float | A | Note agitator |
| `/Hopper/IndexerCurrentAmps` | float | A | Note indexer |
| `/Hopper/ShooterFeedingRollerCurrentAmps` | float | A | Feed roller to shooter |

### Motor currents — Intake

| Signal path | Type | Unit | Notes |
|---|---|---|---|
| `/Intake/IntakeRollerCurrentAmps` | float | A | Ground intake roller |
| `/Intake/IntakePivotCurrentAmps` | float | A | Intake deploy pivot |

### Motor currents — Climber

| Signal path | Type | Unit | Notes |
|---|---|---|---|
| `/Climber/LiftMotorCurrentAmps` | float | A | Climber lift motor |

---

## Subsystem current groupings

| Group name | Signals (count) | Typical peak (A) |
|---|---|---|
| `drive` | Module0–3 Drive + Turn (8) | 60–100A (full sprint) |
| `shooter` | TopRoller, BottomRoller, AngleMotor (3) | 30–40A (spin-up) |
| `hopper` | Agitator, Indexer, FeedingRoller (3) | 5–15A |
| `intake` | IntakeRoller, IntakePivot (2) | 5–20A |
| `climber` | LiftMotor (1) | 10–30A |

---

## Derived quantities (computed by analysis modules)

| Quantity | Formula | Units |
|---|---|---|
| Total current | Σ all motor currents | A |
| Instantaneous power | `/SystemStats/BatteryVoltage` × total current | W |
| Match energy | ∫ power dt (trapezoidal) over match window | Wh |
| Subsystem energy | ∫ (V × subsystem current sum) dt | Wh |

---

## Match period detection

```
Signal: /DriverStation/Enabled, /DriverStation/Autonomous, /DriverStation/MatchTime

Autonomous:  Enabled=True,  Autonomous=True,  MatchTime > 0   (~20s → 0)
Gap:         Enabled=False, Autonomous=True,  MatchTime = 0   (~4–5s between periods)
Teleop:      Enabled=True,  Autonomous=False, MatchTime > 0   (~140s → 0)
Endgame:     Enabled=True,  Autonomous=False, MatchTime ≤ 30  (subset of teleop)
Post-match:  Enabled=False, MatchTime = 0
```

Elapsed time axis: seconds from the first auto-enabled row (t = 0 at auto start).

---

## Observed match example — cmptx_e4 (Elimination Match 4)

| Event | Robot ts | MatchTime | BatteryVoltage |
|---|---|---|---|
| Auto start (Enabled) | 234.9s | 20.0 | 12.82V |
| Auto end (Disabled) | 255.1s | 0.0 | 11.69V |
| Teleop start (Enabled) | 259.3s | 140.0 | 12.77V |
| Match end (Disabled) | 399.9s | 0.0 | 12.13V |

Total match duration: ~165s of robot clock (150s of actual match + ~15s gap/overhead).

---

## Legacy flat-schema CSV (synthetic test data only)

The files in `data/sample/` use an older synthetic flat-schema format, not from real logs:

```
timestamp, match_time, robot_enabled, autonomous,
voltage_battery, current_total,
current_ch00 … current_ch07,
subsystem_drive, subsystem_shooter, subsystem_intake, subsystem_climber
```

Used only for testing the legacy `TelemetryParser` class. Do not confuse with real AKit data.
