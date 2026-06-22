"""Tests for database schema, zone loading, and trip constraints."""

import sqlite3

import pytest

from database.insert import TRIP_COLS, ZONES_FILE, _row_to_native, insert_zones


def _trip_row(**overrides):
    """Minimal valid trip row matching schema.sql constraints."""
    row = {
        "pickup_datetime": "2024-01-15 08:00:00",
        "dropoff_datetime": "2024-01-15 08:20:00",
        "pu_zone_id": 100,
        "do_zone_id": 200,
        "rate_code_id": 1,
        "passenger_count": 2,
        "trip_distance": 3.5,
        "store_fwd_flag": "N",
        "fare_amount": 15.0,
        "extra": 0.5,
        "mta_tax": 0.5,
        "tip_amount": 2.0,
        "tolls_amount": 0.0,
        "improvement_surcharge": 0.3,
        "total_amount": 18.8,
        "congestion_surcharge": 2.5,
        "airport_fee": None,
        "payment_type": 1,
        "trip_duration_sec": 1200,
        "speed_mph": 10.5,
        "tip_pct": 13.33,
        "is_rush_hour": 1,
        "time_of_day": "Morning",
        "fare_per_mile": 4.29,
        "is_airport_trip": 0,
        "pickup_hour": 8,
        "pickup_dow": 0,
        "pickup_date": "2024-01-15",
    }
    row.update(overrides)
    return row


def _insert_trip(conn, **overrides):
    placeholders = ",".join(["?"] * len(TRIP_COLS))
    sql = f"INSERT INTO trips ({','.join(TRIP_COLS)}) VALUES ({placeholders})"
    conn.execute(sql, _row_to_native(_trip_row(**overrides)))


def _seed_minimal_zones(conn):
    """Insert a small zone set including TLC special IDs 264 and 265."""
    rows = [
        (100, "Zone A", "Manhattan", "Yellow Zone"),
        (200, "Zone B", "Queens", "Boro Zone"),
        (264, "N/A", "Unknown", "N/A"),
        (265, "Outside of NYC", "N/A", "N/A"),
    ]
    conn.executemany(
        "INSERT INTO zones (zone_id, zone_name, borough, service_zone) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()


# ── Zone dimension ───────────────────────────────────────────────────────────

def test_all_zones_insert_including_special_ids(db_conn):
    if not ZONES_FILE.exists():
        pytest.skip(f"Missing {ZONES_FILE} — run run_pipeline.py first")

    insert_zones(db_conn)

    count = db_conn.execute("SELECT COUNT(*) FROM zones").fetchone()[0]
    assert count == 265

    zone_264 = db_conn.execute(
        "SELECT zone_name, borough, service_zone FROM zones WHERE zone_id = 264"
    ).fetchone()
    zone_265 = db_conn.execute(
        "SELECT zone_name, borough, service_zone FROM zones WHERE zone_id = 265"
    ).fetchone()

    assert zone_264 is not None
    assert zone_265 is not None
    assert zone_264[1] == "Unknown"
    assert zone_265[0] == "Outside of NYC"


# ── Trip foreign keys ────────────────────────────────────────────────────────

def test_trip_with_zone_265_inserts(db_with_zones):
    _insert_trip(
        db_with_zones,
        pu_zone_id=43,
        do_zone_id=265,
    )

    row = db_with_zones.execute(
        "SELECT pu_zone_id, do_zone_id FROM trips WHERE do_zone_id = 265"
    ).fetchone()
    assert row == (43, 265)


def test_missing_zone_rejected(db_conn):
    _seed_minimal_zones(db_conn)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        _insert_trip(db_conn, pu_zone_id=999, do_zone_id=200)


def test_invalid_rate_code_rejected(db_conn):
    _seed_minimal_zones(db_conn)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        _insert_trip(db_conn, rate_code_id=99)


# ── CHECK constraints ────────────────────────────────────────────────────────

def test_invalid_payment_type_rejected(db_conn):
    _seed_minimal_zones(db_conn)

    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        _insert_trip(db_conn, payment_type=99)


def test_invalid_passenger_count_rejected(db_conn):
    _seed_minimal_zones(db_conn)

    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        _insert_trip(db_conn, passenger_count=0)


def test_negative_fare_rejected(db_conn):
    _seed_minimal_zones(db_conn)

    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        _insert_trip(db_conn, fare_amount=-5.0)
