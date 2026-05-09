"""Project-wide configuration: file paths, column names, and thresholds."""

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
# Telemetry column names  (see docs/telemetry_schema.md)
# ---------------------------------------------------------------------------
TIMESTAMP_COL = "timestamp"
MATCH_TIME_COL = "match_time"
ENABLED_COL = "robot_enabled"
AUTO_COL = "autonomous"
VOLTAGE_COL = "voltage_battery"
CURRENT_COL = "current_total"

PDH_CHANNEL_COLS = [f"current_ch{i:02d}" for i in range(8)]

SUBSYSTEM_COLS = [
    "subsystem_drive",
    "subsystem_shooter",
    "subsystem_intake",
    "subsystem_climber",
]

REQUIRED_COLS = [TIMESTAMP_COL, ENABLED_COL, VOLTAGE_COL, CURRENT_COL]

# ---------------------------------------------------------------------------
# Electrical thresholds
# ---------------------------------------------------------------------------
NOMINAL_VOLTAGE = 12.6       # V — fully charged SLA battery
BROWNOUT_THRESHOLD = 6.8     # V — roboRIO brownout cutoff
LOW_VOLTAGE_WARNING = 9.0    # V — yellow-flag threshold for analysis reports
