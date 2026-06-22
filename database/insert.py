"""
insert.py
=========
Task 2 – Database Design & Implementation
Inserts cleaned trip + zone data into SQLite (default) or PostgreSQL.

Run AFTER run_pipeline.py has completed.

Usage:
    python database/insert.py        (Windows CMD / PowerShell)
    python3 database/insert.py       (macOS / Linux)

Environment variables (optional — set in .env):
    DB_URL     — connection string (default: sqlite:///nyc_taxi.db in project root)
    BATCH_SIZE — rows per INSERT batch (default: 10000)
"""

import os
import sys
import time
import sqlite3
import pandas as pd
from pathlib import Path

# ── Paths — always relative to THIS file, not the working directory ───────────
HERE        = Path(__file__).resolve().parent          # database/
ROOT        = HERE.parent                              # project root
SCHEMA_FILE = HERE / "schema.sql"
DATA_DIR    = ROOT / "data" / "processed"
TRIPS_FILE  = DATA_DIR / "trips_cleaned.parquet"
ZONES_FILE  = DATA_DIR / "zones_clean.csv"

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH    = str(ROOT / "nyc_taxi.db")   # SQLite file in project root
DB_URL     = os.getenv("DB_URL", f"sqlite:///{DB_PATH}")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))

# Parquet column names → DB column names
COLUMN_MAP = {
    "tpep_pickup_datetime":  "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "pulocationid":          "pu_zone_id",
    "dolocationid":          "do_zone_id",
    "ratecodeid":            "rate_code_id",
    "store_and_fwd_flag":    "store_fwd_flag",
}

# DB columns to insert (must match schema.sql)
TRIP_COLS = [
    "pickup_datetime", "dropoff_datetime",
    "pu_zone_id", "do_zone_id", "rate_code_id",
    "passenger_count", "trip_distance", "store_fwd_flag",
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
    "improvement_surcharge", "total_amount", "congestion_surcharge", "airport_fee",
    "payment_type",
    "trip_duration_sec", "speed_mph", "tip_pct",
    "is_rush_hour", "time_of_day", "fare_per_mile", "is_airport_trip",
    "pickup_hour", "pickup_dow", "pickup_date",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    print(f"[insert] Applying schema from {SCHEMA_FILE} …")
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
    print("[insert] Schema applied.")


# ── Zone insertion ────────────────────────────────────────────────────────────

def insert_zones(conn: sqlite3.Connection, zones_path: Path = ZONES_FILE) -> None:
    """Insert zone lookup rows into the zones dimension table."""
    print(f"[insert] Loading zones from {zones_path} …")
    df = pd.read_csv(zones_path)
    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={"locationid": "zone_id", "zone": "zone_name"}, inplace=True, errors="ignore")

    rows = df[["zone_id","zone_name","borough","service_zone"]].to_records(index=False).tolist()
    conn.executemany(
        "INSERT OR IGNORE INTO zones(zone_id, zone_name, borough, service_zone) VALUES (?,?,?,?)",
        rows
    )
    conn.commit()

    actual_count = conn.execute("SELECT COUNT(*) FROM zones").fetchone()[0]
    print(f"[insert] Inserted {actual_count:,} zone records "
          f"({len(rows):,} attempted).")


def _row_to_native(row_dict: dict) -> tuple:
    """
    Convert one row (dict of column -> value) to a tuple of native Python
    types in TRIP_COLS order. Handles numpy scalars (np.float32/int32/...)
    and NaN -> None, which matters for sqlite3 CHECK constraint evaluation —
    numpy scalar types don't always bind/compare the same way native Python
    int/float do.
    """
    out = []
    for col in TRIP_COLS:
        v = row_dict.get(col)
        if v is None:
            out.append(None)
        elif isinstance(v, float) and pd.isna(v):
            out.append(None)
        elif hasattr(v, "item"):       # numpy scalar (np.float32, np.int32, ...)
            item = v.item()
            out.append(None if (isinstance(item, float) and pd.isna(item)) else item)
        else:
            out.append(v)
    return tuple(out)


def insert_trips(conn: sqlite3.Connection) -> None:
    if not TRIPS_FILE.exists():
        print(f"[insert] ERROR: {TRIPS_FILE} not found.")
        print("  → Run  python run_pipeline.py  first, then try again.")
        sys.exit(1)

    import pyarrow.parquet as pq

    print(f"[insert] Streaming enriched trips from {TRIPS_FILE} …")
    pf    = pq.ParquetFile(TRIPS_FILE)
    total = pf.metadata.num_rows

    ph  = ",".join(["?"] * len(TRIP_COLS))
    sql = f"INSERT INTO trips ({','.join(TRIP_COLS)}) VALUES ({ph})"

    inserted = 0
    t0       = time.time()

    print(f"[insert] Inserting {total:,} rows in batches of {BATCH_SIZE:,} …")

    # iter_batches streams row groups from disk instead of materialising
    # the entire 7M+ row file as one pandas DataFrame — this keeps peak
    # memory bounded to roughly one batch's worth of data at a time.
    for batch in pf.iter_batches(batch_size=BATCH_SIZE):
        chunk = batch.to_pandas()
        chunk.rename(columns=COLUMN_MAP, inplace=True)

        for col in TRIP_COLS:
            if col not in chunk.columns:
                chunk[col] = None

        for col in ("pickup_datetime", "dropoff_datetime", "pickup_date"):
            if col in chunk.columns:
                chunk[col] = chunk[col].astype(str)

        records = chunk[TRIP_COLS].to_dict(orient="records")
        rows    = [_row_to_native(r) for r in records]

        conn.executemany(sql, rows)
        conn.commit()
        inserted += len(rows)

        elapsed = time.time() - t0
        rate    = inserted / elapsed if elapsed > 0 else 0
        pct     = inserted / total * 100
        print(f"  {inserted:,} / {total:,} ({pct:.0f}%)  —  {rate:,.0f} rows/s", end="\r")

        # Free this batch before pulling the next one
        del chunk, records, rows

    print(f"\n[insert] Done — {inserted:,} trips inserted in {time.time()-t0:.1f}s.")


def verify(conn: sqlite3.Connection) -> None:
    print("\n── Verification ──────────────────────────────────")
    for table in ("rate_codes", "zones", "trips"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15}  {n:>12,} rows")
    print("──────────────────────────────────────────────────")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DATABASE INSERT")
    print(f"  DB  : {DB_PATH}")
    print(f"  Data: {DATA_DIR}")
    print("=" * 60)

    if not DATA_DIR.exists():
        print(f"\n[insert] ERROR: data/processed/ folder not found at:\n  {DATA_DIR}")
        print("  → Run  python run_pipeline.py  first to generate it.")
        sys.exit(1)

    conn = get_conn()
    try:
        apply_schema(conn)
        insert_zones(conn)
        insert_trips(conn)
        verify(conn)
    finally:
        conn.close()

    print(f"\n[insert] Database saved to: {DB_PATH}")
    print("\nNext step: python backend/app.py")


if __name__ == "__main__":
    main()
