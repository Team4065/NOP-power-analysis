# Telemetry Schema

This document is the canonical reference for FRC Team 4065 telemetry CSV files.
All sample data, parsers, and tests are based on this schema.

---

## File Naming Convention

```
<year>_<event>_<match_type><match_num>.csv
```

Examples:
- `2026_worlds_qm42.csv` — 2026 Worlds, Qualification Match 42
- `2026_sample_match_1.csv` — synthetic sample for development

---

## Column Definitions

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `timestamp` | float | seconds | Elapsed time since match start (wall-clock source: roboRIO) |
| `match_time` | float | seconds | Official DS match timer (counts down from 150 in teleop, 15 in auto) |
| `robot_enabled` | bool | — | `True` when robot is enabled by the Driver Station |
| `autonomous` | bool | — | `True` during the autonomous period |
| `voltage_battery` | float | V | Battery terminal voltage measured by PDH |
| `current_total` | float | A | Total current draw from battery (sum of all PDH channels) |
| `current_ch00` | float | A | PDH channel 0 current (drivetrain left front motor) |
| `current_ch01` | float | A | PDH channel 1 current (drivetrain left rear motor) |
| `current_ch02` | float | A | PDH channel 2 current (drivetrain right front motor) |
| `current_ch03` | float | A | PDH channel 3 current (drivetrain right rear motor) |
| `current_ch04` | float | A | PDH channel 4 current (shooter top motor) |
| `current_ch05` | float | A | PDH channel 5 current (shooter bottom motor) |
| `current_ch06` | float | A | PDH channel 6 current (intake motor) |
| `current_ch07` | float | A | PDH channel 7 current (climber motor) |
| `subsystem_drive` | string | — | Drivetrain state: `"idle"`, `"teleop"`, `"auto"` |
| `subsystem_shooter` | string | — | Shooter state: `"idle"`, `"spinup"`, `"firing"` |
| `subsystem_intake` | string | — | Intake state: `"idle"`, `"intaking"`, `"ejecting"` |
| `subsystem_climber` | string | — | Climber state: `"idle"`, `"deploying"`, `"climbing"` |

### Notes

- Logging rate: ~50 Hz (one row every ~0.02 s)
- `current_total` may differ slightly from the sum of channel currents due to PDH overhead and VREG loads
- Battery voltage below **6.8 V** triggers roboRIO brownout (motors disabled)
- During `robot_enabled = False` (disabled periods), most channel currents drop to near zero

---

## Derived Quantities (computed, not logged)

These are calculated by the analysis modules — not present in raw CSV files.

| Quantity | Formula | Unit |
|----------|---------|------|
| Instantaneous power | `voltage_battery × current_total` | W |
| Energy consumed | `∫ power dt` (trapezoidal) | Wh |
| Internal resistance | slope of `V = V_oc − I × R` | Ω |

---

## Example Row (header + 1 data row)

```
timestamp,match_time,robot_enabled,autonomous,voltage_battery,current_total,current_ch00,current_ch01,current_ch02,current_ch03,current_ch04,current_ch05,current_ch06,current_ch07,subsystem_drive,subsystem_shooter,subsystem_intake,subsystem_climber
0.00,15.00,True,True,12.45,18.3,4.1,3.9,4.0,4.2,0.5,0.5,1.1,0.0,auto,idle,idle,idle
```
