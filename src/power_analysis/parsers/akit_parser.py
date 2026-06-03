"""Parse an AdvantageKit sparse CSV into a normalized match DataFrame.

Key transformations applied by AKitParser.load():
  1. Forward-fill all sparse null cells
  2. Parse "True"/"False" string booleans to Python bool
  3. Extract the match window (Enabled=True, MatchTime > 0)
  4. Build an elapsed_s index starting at 0.0 from the auto start row
  5. Derive current_total = sum of all motor current signals
  6. Produce one current_<subsystem> column per subsystem group
  7. Rename battery voltage to voltage_12v

Output column names are defined in config.py (ELAPSED_COL, VOLTAGE_12V_COL, etc.)
so downstream analysis modules never reference raw AKit signal strings.
"""

from __future__ import annotations

import platform
from pathlib import Path

import numpy as np
import pandas as pd

from power_analysis import config
from power_analysis.utils.logger import get_logger

log = get_logger(__name__)

# AKit CSV marker: at least one column name starts with "/"
_AKIT_MARKER = "/"

# Sentinel for "no match in progress"
_NO_MATCH_TIME = -1.0


class AKitParser:
    """Convert an AKit CSV file to a normalized match DataFrame.

    Parameters
    ----------
    filepath : str | Path
        Path to an AKit-format CSV file.

    Example
    -------
    >>> parser = AKitParser(Path("akit_cmptx_e4.csv"))
    >>> df = parser.load()
    >>> print(df[[config.ELAPSED_COL, config.VOLTAGE_12V_COL]].head())
    """

    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)

    def load(self) -> pd.DataFrame:
        """Load, parse, and return the normalized match DataFrame.

        Returns
        -------
        pd.DataFrame
            Rows: one per AKit sample within the enabled match window.
            Index: integer (reset).
            Columns: see config.py output column constants.

        Raises
        ------
        FileNotFoundError
            If filepath does not exist.
        ValueError
            If the file is not AKit format (no slash-prefixed columns).
        """
        if not self.filepath.exists():
            raise FileNotFoundError(f"Log file not found: {self.filepath}")

        log.info("Loading AKit CSV: %s", self.filepath.name)
        raw = pd.read_csv(self.filepath, dtype=str, low_memory=False)

        self._validate_akit_format(raw)

        # Step 1 — forward-fill sparse AKit data
        raw = raw.ffill()

        # Step 2 — convert numeric columns
        for col in raw.columns:
            if col == "Timestamp":
                continue
            if col in (
                config.AKIT_ENABLED_COL,
                config.AKIT_AUTONOMOUS_COL,
                config.AKIT_BROWNED_OUT_COL,
            ):
                continue  # handled as booleans below
            raw[col] = pd.to_numeric(raw[col], errors="coerce")

        timestamp = pd.to_numeric(raw["Timestamp"], errors="coerce")

        # Step 3 — parse boolean string columns
        enabled = self._parse_bool_col(raw, config.AKIT_ENABLED_COL)
        autonomous = self._parse_bool_col(raw, config.AKIT_AUTONOMOUS_COL)
        browned_out = self._parse_bool_col(raw, config.AKIT_BROWNED_OUT_COL)

        match_time = pd.to_numeric(
            raw.get(config.AKIT_MATCH_TIME_COL, pd.Series(dtype=float)),
            errors="coerce",
        ).fillna(_NO_MATCH_TIME)

        # Step 4 — extract match window: Enabled=True, MatchTime > 0
        in_match = enabled & (match_time > 0)
        match_raw = raw[in_match].copy()
        match_ts = timestamp[in_match]
        match_time_in = match_time[in_match]
        match_enabled = enabled[in_match]
        match_auto = autonomous[in_match]
        match_browned = browned_out[in_match]

        if match_raw.empty:
            log.warning("No enabled match rows found in %s", self.filepath.name)
            return pd.DataFrame()

        # Step 5 — build elapsed_s from first row
        elapsed = (match_ts - match_ts.iloc[0]).values

        # Step 6 — battery voltage
        voltage = pd.to_numeric(
            match_raw.get(config.AKIT_VOLTAGE_COL, pd.Series(dtype=float)),
            errors="coerce",
        ).fillna(0.0).values

        # Step 7 — per-subsystem current columns and total
        subsystem_currents: dict[str, np.ndarray] = {}
        for subsystem, signal_cols in config.AKIT_MOTOR_CURRENT_COLS.items():
            present = [c for c in signal_cols if c in match_raw.columns]
            if present:
                subsystem_arr = (
                    match_raw[present]
                    .apply(pd.to_numeric, errors="coerce")
                    .fillna(0.0)
                    .sum(axis=1)
                    .values
                )
            else:
                subsystem_arr = np.zeros(len(match_raw))
                log.debug("No signals found for subsystem '%s'", subsystem)
            subsystem_currents[subsystem] = subsystem_arr

        current_total = sum(subsystem_currents.values())

        # Step 8 — assemble output DataFrame
        out: dict[str, object] = {
            config.ELAPSED_COL: elapsed,
            config.VOLTAGE_12V_COL: voltage,
            config.CURRENT_TOTAL_COL: current_total,
            config.ENABLED_OUT_COL: match_enabled.values,
            config.AUTONOMOUS_OUT_COL: match_auto.values,
            config.BROWNED_OUT_OUT_COL: match_browned.values,
            config.MATCH_TIME_REMAINING_COL: match_time_in.values,
        }
        for subsystem, arr in subsystem_currents.items():
            out[f"current_{subsystem}"] = arr

        df = pd.DataFrame(out)

        # Cast boolean columns to correct dtype
        for col in (config.ENABLED_OUT_COL, config.AUTONOMOUS_OUT_COL, config.BROWNED_OUT_OUT_COL):
            df[col] = df[col].astype(bool)

        log.info(
            "Parsed %d match rows (%.1fs elapsed) from %s",
            len(df),
            elapsed[-1] if len(elapsed) else 0.0,
            self.filepath.name,
        )
        return df

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_akit_format(df: pd.DataFrame) -> None:
        """Raise ValueError if the DataFrame doesn't look like AKit format."""
        if not any(_AKIT_MARKER in col for col in df.columns):
            raise ValueError(
                f"File does not appear to be AKit format — "
                f"no column names contain '{_AKIT_MARKER}'. "
                f"Found columns: {list(df.columns[:5])}"
            )

    @staticmethod
    def _parse_bool_col(df: pd.DataFrame, col: str) -> pd.Series:
        """Convert a string-boolean AKit column to a boolean Series."""
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        return df[col].map(
            lambda v: str(v).strip().lower() in ("true", "1", "yes")
        ).astype(bool)
