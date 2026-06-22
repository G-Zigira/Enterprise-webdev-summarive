"""Shared pytest fixtures for database tests."""

import sqlite3

import pytest

from database.insert import TRIP_COLS, ZONES_FILE, apply_schema, insert_zones


@pytest.fixture
def db_conn():
    """In-memory SQLite database with schema applied."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def db_with_zones(db_conn):
    """Database with all TLC zones loaded from processed CSV."""
    if not ZONES_FILE.exists():
        pytest.skip(f"Missing {ZONES_FILE} — run run_pipeline.py first")
    insert_zones(db_conn)
    return db_conn
