"""Generate the committed sample log pair in data/sample/.

Trims one real championship elimination match down to:
  1. only the match window (auto through match end, plus a short pre/post buffer)
  2. only the ~25 power-relevant signals this tool analyzes

and writes a small, self-contained `.wpilog` + its converted `.csv`. Both are
small enough to commit to plain git, while remaining real championship data that
exercises the full tool (real brownout, all subsystems).

Why a hand-rolled WPILOG writer:
    robotpy-wpiutil's DataLogWriter binding segfaults at interpreter shutdown on
    some platforms (the file comes out empty). Reading works fine, so we read with
    DataLogReader and re-emit kept records with a minimal pure-Python encoder,
    copying each record's raw payload bytes straight through (no value re-encoding).

Usage:
    PYTHONPATH=src python scripts/make_sample.py \
        --source /path/to/akit_26-05-02_20-10-32_cmptx_e4.wpilog \
        --source-csv /path/to/akit_26-05-02_20-10-32_cmptx_e4.csv \
        --out-dir data/sample --name akit_cmptx_e4_sample
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import pandas as pd
from wpiutil.log import DataLogReader

from power_analysis import config
from power_analysis.parsers._wpilog_convert import convert_wpilog

# Signals the tool actually uses — everything else is dropped from the sample.
KEEP_SIGNALS: set[str] = {
    config.AKIT_VOLTAGE_COL,
    config.AKIT_BROWNED_OUT_COL,
    config.AKIT_BROWNOUT_VOLTAGE_COL,
    config.AKIT_ENABLED_COL,
    config.AKIT_AUTONOMOUS_COL,
    config.AKIT_MATCH_TIME_COL,
    config.AKIT_MATCH_TYPE_COL,
    config.AKIT_MATCH_NUMBER_COL,
    *config.ALL_MOTOR_CURRENT_COLS,
}

# Seconds of context to keep on either side of the enabled match window.
PRE_BUFFER_S = 5.0
POST_BUFFER_S = 3.0


class WpilogWriter:
    """Minimal WPILOG binary encoder (matches the AdvantageKit header format)."""

    def __init__(self, fh, extra_header: str = "AdvantageKit") -> None:
        self.fh = fh
        eh = extra_header.encode("utf-8")
        fh.write(b"WPILOG")
        fh.write(struct.pack("<H", 0x0100))  # version 1.0
        fh.write(struct.pack("<I", len(eh)))
        fh.write(eh)

    def _record(self, entry_id: int, ts_us: int, payload: bytes) -> None:
        # Fixed field widths: entryId=4, payloadSize=4, timestamp=8.
        # Bitfield: (4-1) | (4-1)<<2 | (8-1)<<4 == 0x7F
        self.fh.write(b"\x7f")
        self.fh.write(struct.pack("<I", entry_id))
        self.fh.write(struct.pack("<I", len(payload)))
        self.fh.write(struct.pack("<Q", ts_us))
        self.fh.write(payload)

    def write_start(self, entry_id: int, name: str, type_str: str,
                    metadata: str, ts_us: int) -> None:
        n = name.encode("utf-8")
        t = type_str.encode("utf-8")
        m = metadata.encode("utf-8")
        payload = (
            b"\x00"  # control record type 0 = Start
            + struct.pack("<I", entry_id)
            + struct.pack("<I", len(n)) + n
            + struct.pack("<I", len(t)) + t
            + struct.pack("<I", len(m)) + m
        )
        self._record(0, ts_us, payload)

    def write_data(self, entry_id: int, ts_us: int, payload: bytes) -> None:
        self._record(entry_id, ts_us, payload)


def find_match_window(source_csv: Path) -> tuple[float, float]:
    """Return (t0, t1) in seconds for the enabled match window plus buffers."""
    cols = [config.AKIT_ENABLED_COL, config.AKIT_MATCH_TIME_COL, "Timestamp"]
    df = pd.read_csv(source_csv, usecols=lambda c: c in cols, dtype=str, low_memory=False)
    df = df.ffill()
    ts = pd.to_numeric(df["Timestamp"], errors="coerce")
    enabled = df[config.AKIT_ENABLED_COL].map(
        lambda v: str(v).strip().lower() == "true"
    )
    match_time = pd.to_numeric(df[config.AKIT_MATCH_TIME_COL], errors="coerce")
    in_match = enabled & (match_time > 0)
    if not in_match.any():
        raise SystemExit(f"No enabled match window found in {source_csv}")
    t0 = float(ts[in_match].min()) - PRE_BUFFER_S
    t1 = float(ts[in_match].max()) + POST_BUFFER_S
    return t0, t1


def trim_wpilog(source: Path, dest: Path, t0_s: float, t1_s: float) -> int:
    """Trim source wpilog to KEEP_SIGNALS within [t0, t1]; return record count."""
    t0_us = int(t0_s * 1_000_000)
    t1_us = int(t1_s * 1_000_000)

    entries: dict[int, dict] = {}          # source entry id → {name, type, metadata}
    carry: dict[int, bytes] = {}           # source entry id → last payload before t0
    in_window: list[tuple[int, int, bytes]] = []  # (src entry id, ts_us, payload)

    for rec in DataLogReader(str(source)):
        if rec.isStart():
            d = rec.getStartData()
            if d.name in KEEP_SIGNALS:
                entries[d.entry] = {
                    "name": d.name, "type": d.type, "metadata": d.metadata,
                }
        elif not rec.isControl():
            eid = rec.getEntry()
            if eid not in entries:
                continue
            ts = rec.getTimestamp()
            payload = bytes(rec.getRaw())
            if ts < t0_us:
                carry[eid] = payload          # remember latest pre-window value
            elif ts <= t1_us:
                in_window.append((eid, ts, payload))

    # Assign new sequential entry IDs (1..N) for the kept signals.
    new_id = {src: i + 1 for i, src in enumerate(entries)}

    with dest.open("wb") as fh:
        writer = WpilogWriter(fh)
        # Start records for every kept entry, emitted at the window start.
        for src, info in entries.items():
            writer.write_start(
                new_id[src], info["name"], info["type"], info["metadata"], t0_us
            )
        # Carry-forward each signal's pre-window value at t0 so the window opens
        # with a known value (mirrors forward-fill semantics).
        for src, payload in carry.items():
            writer.write_data(new_id[src], t0_us, payload)
        # In-window records, original timestamps preserved.
        for src, ts, payload in in_window:
            writer.write_data(new_id[src], ts, payload)

    return len(in_window) + len(carry)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True, help="Source .wpilog")
    p.add_argument("--source-csv", type=Path, required=True,
                   help="Source converted .csv (used to locate the match window)")
    p.add_argument("--out-dir", type=Path, default=Path("data/sample"))
    p.add_argument("--name", default="akit_cmptx_e4_sample",
                   help="Base filename (no extension) for the output pair")
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_wpilog = args.out_dir / f"{args.name}.wpilog"
    out_csv = args.out_dir / f"{args.name}.csv"

    print(f"Locating match window in {args.source_csv.name}...")
    t0, t1 = find_match_window(args.source_csv)
    print(f"  window: {t0:.1f}s … {t1:.1f}s ({t1 - t0:.1f}s)")

    print(f"Trimming {args.source.name} → {out_wpilog.name} "
          f"({len(KEEP_SIGNALS)} signals)...")
    n = trim_wpilog(args.source, out_wpilog, t0, t1)
    print(f"  wrote {n} records, {out_wpilog.stat().st_size / 1e6:.2f} MB")

    print(f"Converting {out_wpilog.name} → {out_csv.name}...")
    rows, cols = convert_wpilog(out_wpilog, out_csv)
    print(f"  {rows} rows, {cols} cols, {out_csv.stat().st_size / 1e6:.2f} MB")

    print("Done.")


if __name__ == "__main__":
    main()
