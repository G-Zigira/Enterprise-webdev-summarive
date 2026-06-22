"""
data_loader.py
==============
Task 1 – Data Processing & Cleaning
Step 1: Load raw source files (CSV trip data, zone lookup CSV, shapefile)
        from the data/raw/ folder.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent

# Search paths for trip CSV files
TRIP_CSV_SEARCH = [
    ROOT / "data" / "raw" / "yellow_tripdata_2019-01.csv",
    ROOT / "data" / "yellow_tripdata_2019-01.csv",
    ROOT / "yellow_tripdata_2019-01.csv",
    ROOT / "data" / "raw" / "yellow_tripdata_2024-01.csv",
    ROOT / "data" / "yellow_tripdata_2024-01.csv",
    ROOT / "yellow_tripdata_2024-01.csv",
]

ZONE_CSV_SEARCH = [
    ROOT / "data" / "raw" / "taxi_zone_lookup.csv",
    ROOT / "data" / "taxi_zone_lookup.csv",
    ROOT / "taxi_zone_lookup.csv",
]

SHAPEFILE_SEARCH = [
    ROOT / "data" / "raw" / "taxi_zones.shp",
    ROOT / "data" / "raw" / "taxi_zones" / "taxi_zones.shp",
    ROOT / "data" / "taxi_zones.shp",
    ROOT / "taxi_zones.shp",
]

# Columns we actually need from the trip CSV
# Note: Airport_fee was added in later years (2021+), so it's optional
TRIP_USECOLS = [
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "RatecodeID", "store_and_fwd_flag",
    "PULocationID", "DOLocationID", "payment_type",
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
    "improvement_surcharge", "total_amount", "congestion_surcharge"
]

# Data types for faster loading and memory efficiency
TRIP_DTYPES = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float32",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "category",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float32",
    "extra": "float32",
    "mta_tax": "float32",
    "tip_amount": "float32",
    "tolls_amount": "float32",
    "improvement_surcharge": "float32",
    "total_amount": "float32",
    "congestion_surcharge": "float32"
}

def _find_file(search_paths: List[Path], description: str) -> Path:
    """Find the first existing file in a list of search paths."""
    for path in search_paths:
        if path.exists():
            print(f"[data_loader] Found {description} at: {path}")
            return path
    raise FileNotFoundError(
        f"[data_loader] Could not find {description} in any of these locations:\n"
        + "\n".join(f"  {p}" for p in search_paths)
    )

def load_trips() -> pd.DataFrame:
    """
    Load the yellow taxi trip CSV.
    Returns raw DataFrame — no cleaning applied here.
    """
    path = _find_file(TRIP_CSV_SEARCH, "yellow_tripdata CSV")
    print(f"[data_loader] Loading trips from:\n  {path}")
    df = pd.read_csv(
        path,
        usecols=TRIP_USECOLS,
        dtype=TRIP_DTYPES,
        parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"],
    )
    print(f"[data_loader] Loaded {len(df):,} raw trip records.")
    return df

def load_zones() -> pd.DataFrame:
    """
    Load the taxi zone lookup CSV (dimension table).
    Columns: LocationID, Borough, Zone, service_zone
    """
    path = _find_file(ZONE_CSV_SEARCH, "taxi_zone_lookup.csv")
    print(f"[data_loader] Loading zone lookup from:\n  {path}")
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={"locationid": "zone_id", "zone": "zone_name"}, inplace=True)

    # TLC's lookup includes two special placeholder zones with blank
    # fields: 264 "Unknown" and 265 "Outside of NYC".
    df["zone_name"] = df["zone_name"].fillna("Unknown")
    df["borough"] = df["borough"].fillna("Unknown")
    df["service_zone"] = df["service_zone"].fillna("N/A")

    print(f"[data_loader] Loaded {len(df):,} zone records.")
    return df

def load_spatial():
    """
    Load the taxi zones shapefile.
    Requires geopandas — returns None gracefully if not installed or file missing.
    """
    try:
        import geopandas as gpd
    except ImportError:
        print("[data_loader] NOTE: geopandas not installed — skipping shapefile load.")
        print("  (Optional) Install with: pip install geopandas")
        return None

    try:
        path = _find_file(SHAPEFILE_SEARCH, "taxi_zones.shp")
    except FileNotFoundError as e:
        print(f"[data_loader] NOTE: {e}\n  Skipping shapefile — pipeline will continue without it.")
        return None

    print(f"[data_loader] Loading shapefile from:\n  {path}")
    gdf = gpd.read_file(path)
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    print(f"[data_loader] Loaded {len(gdf):,} spatial zone polygons.")
    return gdf

def load_all():
    """Load all three source files. Shapefile is optional and may return None."""
    trips   = load_trips()
    zones   = load_zones()
    spatial = load_spatial()
    return trips, zones, spatial

if __name__ == "__main__":
    trips, zones, spatial = load_all()
    print("\n── Trips sample ──")
    print(trips.head(3))
    print("\n── Date range ──")
    print(f"  Min pickup: {trips['tpep_pickup_datetime'].min()}")
    print(f"  Max pickup: {trips['tpep_pickup_datetime'].max()}")
    print("\n── Zones sample ──")
    print(zones.head(3))
