

import pandas as pd
import numpy as np

# NYC TLC airport zone IDs
AIRPORT_ZONE_IDS = {1, 132, 138}   # EWR, JFK, LaGuardia

# Rush hour windows 
RUSH_AM_START, RUSH_AM_END = 7, 9      
RUSH_PM_START, RUSH_PM_END = 17, 19    


def _bucket_time(hour: int) -> str:
    if 5  <= hour < 12: return "Morning"
    if 12 <= hour < 17: return "Afternoon"
    if 17 <= hour < 21: return "Evening"
    return "Night"


def add_features(df: pd.DataFrame) -> pd.DataFrame:

    # Ensure datetime columns are parsed
    df["tpep_pickup_datetime"]  = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

    # Feature 1: Trip duration in seconds
  
    if "trip_duration_sec" not in df.columns:
        df["trip_duration_sec"] = (
            df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
        ).dt.total_seconds().astype(int)

    # Feature 2: Average speed in mph
    df["speed_mph"] = (
        df["trip_distance"] / (df["trip_duration_sec"] / 3600)
    ).replace([np.inf, -np.inf], np.nan).round(2)

    # Clamp physically impossible speeds (sensor errors)
    df["speed_mph"] = df["speed_mph"].clip(upper=80)

    # Feature 3: Tip percentage 
    df["tip_pct"] = (
        df["tip_amount"] / df["fare_amount"].replace(0, np.nan) * 100
    ).fillna(0).round(2)

    # Feature 4: Rush-hour flag 
    pickup_hour = df["tpep_pickup_datetime"].dt.hour
    pickup_dow  = df["tpep_pickup_datetime"].dt.dayofweek   # 0=Mon, 6=Sun

    is_weekday = pickup_dow < 5
    is_am_rush = (pickup_hour >= RUSH_AM_START) & (pickup_hour < RUSH_AM_END)
    is_pm_rush = (pickup_hour >= RUSH_PM_START) & (pickup_hour < RUSH_PM_END)

    df["is_rush_hour"] = (is_weekday & (is_am_rush | is_pm_rush)).astype(int)

    # Feature 5: Time-of-day bucket 
    df["time_of_day"] = pickup_hour.apply(_bucket_time)

    # Feature 6: Fare per mile 
    df["fare_per_mile"] = (
        df["fare_amount"] / df["trip_distance"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).round(2)

    # Feature 7: Airport trip flag 
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
