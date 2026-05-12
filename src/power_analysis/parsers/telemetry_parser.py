"""Parse FRC telemetry CSV logs into DataFrames.

See docs/telemetry_schema.md for the expected column layout.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from power_analysis import config  # noqa: F401


class TelemetryParser:
    """Load and validate an FRC telemetry CSV file.

    Example
    -------
    >>> parser = TelemetryParser("data/sample/2026_sample_match_1.csv")
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
        # TODO: Raise FileNotFoundError if self.filepath does not exist
        # TODO: Load the CSV with pd.read_csv
        # TODO: Call self._validate_columns(df) to check required columns
        # TODO: Convert the timestamp column to float and set it as the index
        # TODO: Return the cleaned DataFrame
        raise NotImplementedError("Implement TelemetryParser.load()")

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Raise ValueError listing any missing required columns.

        Parameters
        ----------
        df : pd.DataFrame
            The freshly loaded DataFrame to validate.
        """
        # TODO: Get the list of required columns from config.REQUIRED_COLS
        # TODO: Find any columns that are in REQUIRED_COLS but NOT in df.columns
        # TODO: If any are missing, raise ValueError with a helpful message listing them
        raise NotImplementedError("Implement TelemetryParser._validate_columns()")
