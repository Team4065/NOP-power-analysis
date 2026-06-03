"""Parse FRC telemetry CSV logs into DataFrames.

See docs/telemetry_schema.md for the expected column layout.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from power_analysis import config


class TelemetryParser:
    """Load and validate a legacy flat-schema FRC telemetry CSV file.

    For AdvantageKit logs, use ``AKitParser`` instead. This parser remains for
    teams that export telemetry in the older flat CSV schema.

    Example
    -------
    >>> parser = TelemetryParser("match.csv")
    >>> df = parser.load()
    >>> df.head()
    """

    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)

    def load(self) -> pd.DataFrame:
        """Load and validate the telemetry CSV.

        Returns
        -------
        pd.DataFrame
            DataFrame indexed by ``timestamp`` with all telemetry columns.

        Raises
        ------
        FileNotFoundError
            If ``self.filepath`` does not exist.
        ValueError
            If any required columns are missing from the file.
        """
        if not self.filepath.exists():
            raise FileNotFoundError(f"Telemetry file not found: {self.filepath}")
        df = pd.read_csv(self.filepath)
        self._validate_columns(df)
        df[config.TIMESTAMP_COL] = df[config.TIMESTAMP_COL].astype(float)
        return df.set_index(config.TIMESTAMP_COL, drop=False)

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Raise ValueError listing any missing required columns.

        Parameters
        ----------
        df : pd.DataFrame
            The freshly loaded DataFrame to validate.
        """
        missing = [col for col in config.REQUIRED_COLS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
