# Glossary

FRC Team 4065 power analysis — canonical term definitions.

---

## AKit / AdvantageKit

A structured logging framework for FRC robots (by Team 6328). Logs robot signals as a sparse time series: each signal only appears in a row when its value changes; all other timestamps are `null` and must be forward-filled before analysis.

## AKit signal path

The hierarchical string key used to identify a logged signal, e.g. `/SystemStats/BatteryVoltage` or `/Drive/Module0/DriveCurrentAmps`. Paths use forward-slash separators on all platforms.

## wpilog

Binary DataLog file format produced by WPILib / AdvantageKit. Files carry the `.wpilog` extension. Must be converted to CSV before analysis. Conversion uses `robotpy-wpiutil` (`DataLogReader`).

## PDH (Power Distribution Hub)

REV Robotics Power Distribution Hub. The 2026 Team 4065 robot uses an **older PDH model with no CAN bus connection**, so all `/PowerDistribution/*` signals are always zero in these logs. Total current must be derived by summing individual motor current signals.

## PDP (Power Distribution Panel)

Older CTRE power distribution hardware; predecessor to the PDH. Referenced for context only — Team 4065 uses PDH.

## 12V main battery

Standard FRC lead-acid battery (12V nominal). The robot draws all power from this battery through the PDH. Voltage is monitored at the roboRIO via `/SystemStats/BatteryVoltage`.

## BatteryVoltage

`/SystemStats/BatteryVoltage` — the battery terminal voltage as measured by the roboRIO analog input. This is the primary voltage signal used in all analysis. Units: Volts.

## BatteryCurrent (roboRIO input — not total)

`/SystemStats/BatteryCurrent` — the roboRIO's own 12V input current (~0.4A). **Not** the main battery current. Do not use for total current estimation.

## BrownedOut

`/SystemStats/BrownedOut` — a boolean signal (`True`/`False`) set by the roboRIO when battery voltage drops below the brownout threshold. Use this signal directly for brownout detection rather than applying threshold math to `BatteryVoltage`.

## Brownout threshold

The voltage level at which the roboRIO triggers a brownout protection event. Actual configured value: **6.0V** (read from `/SystemStats/BrownoutVoltage`). Note: the default WPILib value is 6.8V, but Team 4065 configures 6.0V.

## MatchTime

`/DriverStation/MatchTime` — the Driver Station match timer, counting down in seconds within the current period. Key values:
- `-1` or `0.0` with Enabled=False → no match in progress
- `~20` at autonomous start → counts down to 0
- `~140` at teleop start → counts down to 0
- `≤ 30` during teleop → endgame period

## MatchType

`/DriverStation/MatchType` — integer indicating match category:
- `0` = None (practice/test session)
- `1` = Practice match
- `2` = Qualification match
- `3` = Elimination / playoff match

## Session label

Human-readable string derived from MatchType and MatchNumber, used in plot titles and report headers:
- `practice-session` (MatchType 0 or MatchTime always -1)
- `practice-match` (MatchType 1)
- `qual-{N}` (MatchType 2)
- `elimination-{N}` (MatchType 3)

## Match periods

| Period | Condition | Typical duration |
|---|---|---|
| **Auto** | Enabled=True, Autonomous=True | ~15s (MatchTime ≈ 20 → 0) |
| **Teleop** | Enabled=True, Autonomous=False, MatchTime > 30 | ~110s |
| **Endgame** | Enabled=True, Autonomous=False, MatchTime ≤ 30 | ~30s |

## Endgame boundary

MatchTime ≤ `ENDGAME_SECONDS` (30) during the teleop period. Used to draw the third vertical line on plots.

## Subsystem groups

Named groupings of motor current signals summed for per-subsystem power analysis:

| Group | Signals |
|---|---|
| `drive` | 4× `/Drive/Module{i}/DriveCurrentAmps` + 4× `/Drive/Module{i}/TurnCurrentAmps` |
| `shooter` | TopRollerMotor, BottomRollerMotor, AngleMotor |
| `hopper` | Agitator, Indexer, ShooterFeedingRoller |
| `intake` | IntakeRoller, IntakePivot |
| `climber` | LiftMotor |

## Total current (derived)

Sum of all subsystem motor current signals. This is the best available estimate of main battery current draw. Unmeasured loads (radio, VRM outputs, indicator lights) are excluded and noted in tool output.

## Daly division

One of the FRC World Championship event subdivisions. Files with `_daly` suffix are from Daly division practice/qualification rounds.

## cmptx (championship)

World Championship final rounds. Files with `_cmptx` suffix are championship elimination matches. Most relevant for match power analysis.

## Energy (Wh)

Electrical energy = ∫ Power dt, converted to Watt-hours. Computed via trapezoidal integration over the match window.

## Power (W)

Instantaneous electrical power = Voltage × Current (Watts).
