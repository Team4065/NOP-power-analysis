"""Project-wide configuration: file paths, AKit signal constants, and thresholds."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"


def season_raw_dir(year: int) -> Path:
    return DATA_DIR / "seasons" / str(year) / "raw"


def season_processed_dir(year: int) -> Path:
    return DATA_DIR / "seasons" / str(year) / "processed"


# ---------------------------------------------------------------------------
# AKit signal paths  (see docs/telemetry_schema.md)
# ---------------------------------------------------------------------------

# Battery / power
AKIT_VOLTAGE_COL = "/SystemStats/BatteryVoltage"
AKIT_BROWNED_OUT_COL = "/SystemStats/BrownedOut"
AKIT_BROWNOUT_VOLTAGE_COL = "/SystemStats/BrownoutVoltage"

# Driver Station / match state
AKIT_ENABLED_COL = "/DriverStation/Enabled"
AKIT_AUTONOMOUS_COL = "/DriverStation/Autonomous"
AKIT_MATCH_TIME_COL = "/DriverStation/MatchTime"
AKIT_MATCH_TYPE_COL = "/DriverStation/MatchType"
AKIT_MATCH_NUMBER_COL = "/DriverStation/MatchNumber"

# Subsystem motor current signal paths grouped by subsystem.
# Total battery current = sum of all signals across all groups.
# PDH channels (/PowerDistribution/*) are always 0 on this robot — not used.
AKIT_MOTOR_CURRENT_COLS: dict[str, list[str]] = {
    "drive": [
        "/Drive/Module0/DriveCurrentAmps",
        "/Drive/Module0/TurnCurrentAmps",
        "/Drive/Module1/DriveCurrentAmps",
        "/Drive/Module1/TurnCurrentAmps",
        "/Drive/Module2/DriveCurrentAmps",
        "/Drive/Module2/TurnCurrentAmps",
        "/Drive/Module3/DriveCurrentAmps",
        "/Drive/Module3/TurnCurrentAmps",
    ],
    "shooter": [
        "/Shooter/TopRollerMotorCurrentAmps",
        "/Shooter/BottomRollerMotorCurrentAmps",
        "/Shooter/AngleMotorCurrentAmps",
    ],
    "hopper": [
        "/Hopper/AgitatorCurrentAmps",
        "/Hopper/IndexerCurrentAmps",
        "/Hopper/ShooterFeedingRollerCurrentAmps",
    ],
    "intake": [
        "/Intake/IntakeRollerCurrentAmps",
        "/Intake/IntakePivotCurrentAmps",
    ],
    "climber": [
        "/Climber/LiftMotorCurrentAmps",
    ],
}

# Flat list of all motor current columns (for convenience)
ALL_MOTOR_CURRENT_COLS: list[str] = [
    col for cols in AKIT_MOTOR_CURRENT_COLS.values() for col in cols
]

# Normalized output column names (AKitParser produces these)
ELAPSED_COL = "elapsed_s"
VOLTAGE_12V_COL = "voltage_12v"
CURRENT_TOTAL_COL = "current_total"
ENABLED_OUT_COL = "enabled"
AUTONOMOUS_OUT_COL = "autonomous"
BROWNED_OUT_OUT_COL = "browned_out"
MATCH_TIME_REMAINING_COL = "match_time_remaining"

# ---------------------------------------------------------------------------
# Match type labels
# ---------------------------------------------------------------------------
MATCH_TYPE_LABELS: dict[int, str] = {
    0: "practice-session",
    1: "practice-match",
    2: "qual",
    3: "elimination",
}

# ---------------------------------------------------------------------------
# Electrical thresholds
# ---------------------------------------------------------------------------
NOMINAL_VOLTAGE = 12.6      # V — fully charged SLA battery
BROWNOUT_THRESHOLD = 6.0    # V — Team 4065 configured value (from /SystemStats/BrownoutVoltage)
LOW_VOLTAGE_WARNING = 9.0   # V — yellow-flag threshold for analysis reports
ENDGAME_SECONDS = 30        # s — MatchTime threshold for endgame period annotation

# ---------------------------------------------------------------------------
# Legacy flat-schema constants (TelemetryParser / synthetic test data only)
# Do not use for AKit real data.
# ---------------------------------------------------------------------------
TIMESTAMP_COL = "timestamp"
MATCH_TIME_COL = "match_time"
LEGACY_ENABLED_COL = "robot_enabled"
LEGACY_AUTO_COL = "autonomous"
LEGACY_VOLTAGE_COL = "voltage_battery"
LEGACY_CURRENT_COL = "current_total"
PDH_CHANNEL_COLS = [f"current_ch{i:02d}" for i in range(8)]
SUBSYSTEM_COLS = [
    "subsystem_drive",
    "subsystem_shooter",
    "subsystem_intake",
    "subsystem_climber",
]
REQUIRED_COLS = [TIMESTAMP_COL, LEGACY_ENABLED_COL, LEGACY_VOLTAGE_COL, LEGACY_CURRENT_COL]

# Backward-compatible aliases used by existing TelemetryParser tests
VOLTAGE_COL = LEGACY_VOLTAGE_COL
CURRENT_COL = LEGACY_CURRENT_COL
ENABLED_COL = LEGACY_ENABLED_COL
