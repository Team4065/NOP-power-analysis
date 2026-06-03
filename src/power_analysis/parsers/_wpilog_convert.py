"""Internal wpilog → CSV converter using robotpy-wpiutil.

This is a private module; use AKitIngester.convert_all() as the public API.
Logic adapted from championship_logs/scripts/wpilog_to_csv.py.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd


def _encode(type_str: str, rec) -> str | None:
    t = type_str
    try:
        if t == "double":
            return str(rec.getDouble())
        if t == "float":
            return str(rec.getFloat())
        if t == "int64":
            return str(rec.getInteger())
        if t == "boolean":
            return str(rec.getBoolean())
        if t == "string":
            return rec.getString()
        if t == "double[]":
            return ",".join(str(v) for v in rec.getDoubleArray())
        if t == "float[]":
            return ",".join(str(v) for v in rec.getFloatArray())
        if t == "int64[]":
            return ",".join(str(v) for v in rec.getIntegerArray())
        if t == "boolean[]":
            return ",".join(str(v) for v in rec.getBooleanArray())
        if t == "string[]":
            return ",".join(rec.getStringArray())
        return bytes(rec.getRaw()).hex("-")
    except Exception:
        return None


def convert_wpilog(wpilog_path: Path, output_path: Path) -> tuple[int, int]:
    """Read wpilog_path, write AKit-format CSV to output_path.

    Returns (row_count, column_count).
    Requires robotpy-wpiutil to be installed.
    """
    from wpiutil.log import DataLogReader  # noqa: PLC0415

    entries: dict[int, dict] = {}
    signal_data: dict[str, dict] = defaultdict(dict)

    for rec in DataLogReader(str(wpilog_path)):
        if rec.isStart():
            d = rec.getStartData()
            entries[d.entry] = {"name": d.name, "type": d.type}
        elif not rec.isControl():
            eid = rec.getEntry()
            if eid not in entries:
                continue
            info = entries[eid]
            val = _encode(info["type"], rec)
            if val is not None:
                ts_secs = rec.getTimestamp() / 1_000_000.0
                signal_data[info["name"]][ts_secs] = val

    series = {
        name: pd.Series(ts_vals)
        for name, ts_vals in sorted(signal_data.items())
    }
    df = pd.DataFrame(series)
    df.index.name = "Timestamp"
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.to_csv(output_path, na_rep="null")

    return len(df), len(df.columns)
