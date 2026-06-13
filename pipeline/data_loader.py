"""
data_loader.py
==============
Task 1 – Data Processing & Cleaning
Step 1: Load raw source files (parquet, CSV, shapefile) into memory.

Usage:
    from pipeline.data_loader import load_all
    trips, zones, spatial = load_all()
"""

import os
import pandas as pd
import geopandas as gpd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent.parent / "data"
PARQUET_PATH  = ROOT / "yellow_tripdata_2024-01.parquet"
ZONE_CSV_PATH = ROOT / "taxi_zone_lookup.csv"
SHAPEFILE_PATH = ROOT / "taxi_zones" / "taxi_zones.shp"


def load_trips(path: Path = PARQUET_PATH) -> pd.DataFrame:
    """
    Load the yellow taxi trip parquet file.
    Returns raw DataFrame — no cleaning applied here.
    """
    print(f"[data_loader] Loading trips from {path} …")
    if not path.exists():
        raise FileNotFoundError(
            f"Parquet file not found at {path}.\n"
            "Download from: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
        )
    df = pd.read_parquet(path)
    print(f"[data_loader] Loaded {len(df):,} raw trip records.")
    return df


def load_zones(path: Path = ZONE_CSV_PATH) -> pd.DataFrame:
    """
    Load the taxi zone lookup CSV (dimension table).
    Columns: LocationID, Borough, Zone, service_zone
    """
    print(f"[data_loader] Loading zone lookup from {path} …")
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={"locationid": "zone_id", "zone": "zone_name"}, inplace=True)
    print(f"[data_loader] Loaded {len(df):,} zone records.")
    return df


def load_spatial(path: Path = SHAPEFILE_PATH) -> gpd.GeoDataFrame:
    """
    Load the taxi zones shapefile (spatial metadata).
    Returns a GeoDataFrame with polygon geometries.
    """
    print(f"[data_loader] Loading shapefile from {path} …")
    gdf = gpd.read_file(path)
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    print(f"[data_loader] Loaded {len(gdf):,} spatial zone polygons.")
    return gdf


def load_all() -> tuple[pd.DataFrame, pd.DataFrame, gpd.GeoDataFrame]:
    """
    Convenience function — load all three source files at once.

    Returns
    -------
    trips   : raw trip DataFrame
    zones   : zone lookup DataFrame
    spatial : zone spatial GeoDataFrame
    """
    trips   = load_trips()
    zones   = load_zones()
    spatial = load_spatial()
    return trips, zones, spatial


if __name__ == "__main__":
    trips, zones, spatial = load_all()
    print("\n── Trips sample ──")
    print(trips.head(3))
    print("\n── Zones sample ──")
    print(zones.head(3))
    print("\n── Spatial sample ──")
    print(spatial[["objectid", "zone", "borough", "geometry"]].head(3))
