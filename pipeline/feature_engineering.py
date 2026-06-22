"""
feature_engineering.py
=======================
Task 1 – Data Processing & Cleaning
Step 3: Compute derived features from cleaned trip data.

Derived features (justified below):
  1. trip_duration_sec   — fundamental time metric for speed & efficiency analysis
  2. speed_mph           — reveals traffic patterns; anomaly detection for outliers
  3. tip_pct             — normalised tipping behaviour independent of fare amount
  4. is_rush_hour        — binary flag for demand modelling (weekdays 7–9am, 5–7pm)
  5. time_of_day_bucket  — categorical: Morning / Afternoon / Evening / Night
  6. fare_per_mile       — price efficiency metric; varies by route & time
  7. is_airport_trip     — binary flag; JFK=132, LGA=138, EWR=1 — higher-value segment

Usage:
    from pipeline.feature_engineering import add_features
    enriched_df = add_features(cleaned_df)
"""

import pandas as pd
import numpy as np

# NYC TLC airport zone IDs
AIRPORT_ZONE_IDS = {1, 132, 138}   # EWR, JFK, LaGuardia

# Rush hour windows (weekday only)
RUSH_AM_START, RUSH_AM_END = 7, 9      # 07:00–09:59
RUSH_PM_START, RUSH_PM_END = 17, 19    # 17:00–19:59


def _bucket_time(hour: int) -> str:
    """Map hour (0-23) to a named time-of-day bucket."""
    if 5  <= hour < 12: return "Morning"
    if 12 <= hour < 17: return "Afternoon"
    if 17 <= hour < 21: return "Evening"
    return "Night"


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all derived feature columns to the cleaned trips DataFrame.

    All new columns are appended; original columns are untouched.

    Parameters
    ----------
    df : cleaned trips DataFrame (output of clean.clean_trips)

    Returns
    -------
    df : same DataFrame with additional derived columns
    """
    # NOTE: no df.copy() here — clean_trips() already returns a fresh
    # DataFrame, and copying a 7M+ row frame again roughly doubles peak
    # memory at the most memory-constrained point in the pipeline. We
    # mutate in place instead.

    # Ensure datetime columns are parsed
    df["tpep_pickup_datetime"]  = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

    # Feature 1: Trip duration (seconds) 
    # Justification: base metric for all time-based analysis.
    # Already computed in clean.py if present; recompute for safety.
    if "trip_duration_sec" not in df.columns:
        df["trip_duration_sec"] = (
            df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
        ).dt.total_seconds().astype(int)

    # Feature 2: Average speed (mph) 
    # Justification: speed correlates with traffic congestion and time of day.
    # speed = distance / time. Guard against zero division.
    df["speed_mph"] = (
        df["trip_distance"] / (df["trip_duration_sec"] / 3600)
    ).replace([np.inf, -np.inf], np.nan).round(2)

    # Clamp physically impossible speeds (sensor errors)
    df["speed_mph"] = df["speed_mph"].clip(upper=80)

    # Feature 3: Tip percentage 
    # Justification: normalised tip reveals tipping behaviour independent of fare.
    # Cash tips are not recorded by TLC — result is 0.0 for cash trips.
    df["tip_pct"] = (
        df["tip_amount"] / df["fare_amount"].replace(0, np.nan) * 100
    ).fillna(0).round(2)

    # Feature 4: Rush-hour flag 
    # Justification: demand modelling; rush-hour trips often have higher fares.
    pickup_hour = df["tpep_pickup_datetime"].dt.hour
    pickup_dow  = df["tpep_pickup_datetime"].dt.dayofweek   # 0=Mon, 6=Sun

    is_weekday = pickup_dow < 5
    is_am_rush = (pickup_hour >= RUSH_AM_START) & (pickup_hour < RUSH_AM_END)
    is_pm_rush = (pickup_hour >= RUSH_PM_START) & (pickup_hour < RUSH_PM_END)

    df["is_rush_hour"] = (is_weekday & (is_am_rush | is_pm_rush)).astype(int)

    # Feature 5: Time-of-day bucket 
    # Justification: coarser temporal grouping for dashboard filtering.
    df["time_of_day"] = pickup_hour.apply(_bucket_time)

    # Feature 6: Fare per mile 
    # Justification: price efficiency metric; highlights route pricing anomalies.
    df["fare_per_mile"] = (
        df["fare_amount"] / df["trip_distance"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).round(2)

    # Feature 7: Airport trip flag 
    # Justification: airport segment is revenue-critical; avg fare ~2.4× city avg.
    df["is_airport_trip"] = (
        df["pulocationid"].isin(AIRPORT_ZONE_IDS) |
        df["dolocationid"].isin(AIRPORT_ZONE_IDS)
    ).astype(int)

    # Convenience datetime columns for database inserts 
    df["pickup_date"] = df["tpep_pickup_datetime"].dt.date
    df["pickup_hour"] = pickup_hour
    df["pickup_dow"]  = pickup_dow

    print(f"[feature_engineering] Added 7 derived features. "
          f"DataFrame now has {len(df.columns)} columns.")
    return df


def summary(df: pd.DataFrame) -> None:
    """Print a quick feature summary to stdout."""
    features = ["trip_duration_sec","speed_mph","tip_pct","is_rush_hour",
                "time_of_day","fare_per_mile","is_airport_trip"]
    print("\n── Feature Summary ──────────────────────────────")
    for f in features:
        if f in df.columns:
            col = df[f]
            if col.dtype == object or f in ("time_of_day",):
                print(f"  {f:22s}  {col.value_counts().to_dict()}")
            else:
                print(f"  {f:22s}  mean={col.mean():.2f}  "
                      f"min={col.min():.2f}  max={col.max():.2f}")


if __name__ == "__main__":
    from pipeline.data_loader import load_trips
    from pipeline.clean import clean_trips

    raw        = load_trips()
    cleaned, _ = clean_trips(raw)
    enriched   = add_features(cleaned)
    summary(enriched)
