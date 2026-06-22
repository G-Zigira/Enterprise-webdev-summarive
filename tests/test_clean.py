import pandas as pd
import pytest
from pipeline.clean import clean_trips

def make_good_row():
    return {
        "VendorID": 1,
        "tpep_pickup_datetime": "2019-01-15 08:00:00",
        "tpep_dropoff_datetime": "2019-01-15 08:20:00",
        "passenger_count": 2,
        "trip_distance": 3.5,
        "RatecodeID": 1,
        "store_and_fwd_flag": "N",
        "PULocationID": 100,
        "DOLocationID": 200,
        "payment_type": 1,
        "fare_amount": 15.0,
        "extra": 0.5,
        "mta_tax": 0.5,
        "tip_amount": 2.0,
        "tolls_amount": 0.0,
        "improvement_surcharge": 0.3,
        "total_amount": 18.8,
        "congestion_surcharge": 2.5,
    }

def make_df(*overrides):
    rows = [make_good_row()]
    for o in overrides:
        row = make_good_row()
        row.update(o)
        rows.append(row)
    return pd.DataFrame(rows)

# ── Good row survives ──────────────────────────────────────────
def test_good_row_survives():
    df, _ = clean_trips(make_df())
    assert len(df) == 1

# ── Fare outliers ──────────────────────────────────────────────
def test_fare_too_low_dropped():
    df, _ = clean_trips(make_df({"fare_amount": 1.0}))
    assert len(df) == 1  # bad row dropped, good row kept

def test_fare_too_high_dropped():
    df, _ = clean_trips(make_df({"fare_amount": 600.0}))
    assert len(df) == 1

# ── Duration outliers ──────────────────────────────────────────
def test_negative_duration_dropped():
    df, _ = clean_trips(make_df({
        "tpep_pickup_datetime":  "2019-01-15 08:20:00",
        "tpep_dropoff_datetime": "2019-01-15 08:00:00"
    }))
    assert len(df) == 1

def test_duration_too_long_dropped():
    df, _ = clean_trips(make_df({
        "tpep_dropoff_datetime": "2019-01-15 12:00:01"  # >3hrs
    }))
    assert len(df) == 1

# ── Date range ─────────────────────────────────────────────────
def test_out_of_range_date_dropped():
    df, _ = clean_trips(make_df({
        "tpep_pickup_datetime":  "2024-01-15 08:00:00",
        "tpep_dropoff_datetime": "2024-01-15 08:20:00"
    }))
    assert len(df) == 1

# ── Passenger count ────────────────────────────────────────────
def test_zero_passengers_dropped():
    df, _ = clean_trips(make_df({"passenger_count": 0}))
    assert len(df) == 1

def test_too_many_passengers_dropped():
    df, _ = clean_trips(make_df({"passenger_count": 9}))
    assert len(df) == 1

# ── Invalid codes ──────────────────────────────────────────────
def test_invalid_payment_type_dropped():
    df, _ = clean_trips(make_df({"payment_type": 99}))
    assert len(df) == 1

def test_invalid_rate_code_dropped():
    df, _ = clean_trips(make_df({"RatecodeID": 99}))
    assert len(df) == 1

# ── Null critical fields ───────────────────────────────────────
def test_null_fare_dropped():
    df, _ = clean_trips(make_df({"fare_amount": None}))
    assert len(df) == 1

def test_null_pickup_location_dropped():
    df, _ = clean_trips(make_df({"PULocationID": None}))
    assert len(df) == 1
