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

#  Config 
DB_URL      = os.getenv("DB_URL", "sqlite:///nyc_taxi.db")
BATCH_SIZE  = int(os.getenv("BATCH_SIZE", "10000"))
SCHEMA_FILE = Path(__file__).parent / "schema.sql"
DATA_DIR    = Path("data/processed")

TRIPS_FILE  = DATA_DIR / "trips_cleaned.parquet"
ZONES_FILE  = DATA_DIR / "zones_clean.csv"

# Columns in trips parquet are renamed to match DB schematics
COLUMN_MAP = {
    "tpep_pickup_datetime":  "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "pulocationid":          "pu_zone_id",
    "dolocationid":          "do_zone_id",
    "ratecodeid":            "rate_code_id",
    "store_and_fwd_flag":    "store_fwd_flag",
}

# Columns to write to the trips table and they must match schema.sql
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


#  SQLite helpers 

def get_sqlite_conn(path: str = "nyc_taxi.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")   #  writes faster
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def apply_schema(conn: sqlite3.Connection, schema_path: Path = SCHEMA_FILE) -> None:
    """Execute schema.sql against the connection."""
    print(f"[insert] Applying schema from {schema_path} …")
    sql = schema_path.read_text(encoding="utf-8")
    # Removes PostgreSQL-only comments/syntax for SQLite
    conn.executescript(sql)
    conn.commit()
    print("[insert] Schema applied.")


#  Zone insertion 

def insert_zones(conn: sqlite3.Connection, zones_path: Path = ZONES_FILE) -> None:
    """Insert zone lookup rows into the zones dimension table."""
    print(f"[insert] Loading zones from {zones_path} …")
    df = pd.read_csv(zones_path)
    # Normalises the column names
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={"locationid": "zone_id", "zone": "zone_name"}, inplace=True, errors="ignore")

    df["zone_name"]    = df["zone_name"].fillna("Unknown").replace("", "Unknown")
    df["borough"]      = df["borough"].fillna("Unknown").replace("", "Unknown")
    df["service_zone"] = df["service_zone"].fillna("N/A").replace("", "N/A")

    rows = df[["zone_id","zone_name","borough","service_zone"]].to_records(index=False).tolist()
    conn.executemany(
        "INSERT OR IGNORE INTO zones(zone_id, zone_name, borough, service_zone) VALUES (?,?,?,?)",
        rows
    )
    conn.commit()
    print(f"[insert] Inserted {len(rows):,} zone records.")


#  Trip insertion 
def insert_trips(conn: sqlite3.Connection, trips_path: Path = TRIPS_FILE) -> None:
    """
    Batch-insert all cleaned trip rows.
    Uses chunked reads to stay memory-efficient on large parquet files.
    """
    if not trips_path.exists():
        print(f"[insert] ERROR: {trips_path} not found. Run run_pipeline.py first.")
        sys.exit(1)

    print(f"[insert] Loading enriched trips from {trips_path} …")
    df = pd.read_parquet(trips_path)

    #  Renames the columns to match DB schema 
    df.rename(columns=COLUMN_MAP, inplace=True)

    #  Ensure all required columns exist (fill missing with None)
    for col in TRIP_COLS:
        if col not in df.columns:
            df[col] = None

    # Coerce types for SQLite compatibility 
    df["pickup_datetime"]  = df["pickup_datetime"].astype(str)
    df["dropoff_datetime"] = df["dropoff_datetime"].astype(str)
    if "pickup_date" in df.columns:
        df["pickup_date"] = df["pickup_date"].astype(str)

    df = df[TRIP_COLS]   # keeps only theschema columns in order

    total     = len(df)
    inserted  = 0
    t_start   = time.time()

    placeholders = ",".join(["?"] * len(TRIP_COLS))
    sql = f"INSERT INTO trips ({','.join(TRIP_COLS)}) VALUES ({placeholders})"

    print(f"[insert] Inserting {total:,} rows in batches of {BATCH_SIZE:,} …")

    for start in range(0, total, BATCH_SIZE):
        chunk = df.iloc[start : start + BATCH_SIZE]
        # Converts each row to a plain Python tuple (sqlite3 requires it)
        rows = [tuple(r) for r in chunk.itertuples(index=False, name=None)]
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


#  Verification

def verify(conn: sqlite3.Connection) -> None:
    print("\n── Verification ──────────────────────────────────")
    for table in ("rate_codes", "zones", "trips"):
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:<15} {count:>12,} rows")
    print("─" * 48)


# Main 
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
