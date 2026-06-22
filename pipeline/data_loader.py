"""
data_loader.py
==============
Task 1 – Data Processing & Cleaning
Step 1: Load raw source files (CSV trip data, zone lookup CSV, shapefile)
        from the data/raw/ folder.

The trip data file is named yellow_tripdata_2019-01.csv and contains
January 2019 NYC Yellow Taxi trip records. It's ~650MB, which exceeds
GitHub's 100MB file limit, so it's hosted externally — see the README
"Dataset" section for the download link and place it in data/raw/
before running the pipeline. taxi_zone_lookup.csv and the shapefile are
small enough to ship directly in this repository.

Usage:
    from pipeline.data_loader import load_trips, load_zones, load_spatial
    trips   = load_trips()
    zones   = load_zones()
    spatial = load_spatial()   # returns None if geopandas/shapefile unavailable
"""

import pandas as pd
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
# ROOT is the project root (one level above the pipeline/ folder)
ROOT = Path(__file__).resolve().parent.parent

# Primary filename is yellow_tripdata_2019-01.csv (correct TLC naming for
# the January 2019 data it actually contains). The 2024-01 variants are
# kept as fallbacks in case an older renamed copy is still in use.
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

# Columns we actually need from the trip CSV — reading only these keeps
# memory usage manageable on a 650MB / 7.6M-row file.
TRIP_USECOLS = [
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "RatecodeID", "store_and_fwd_flag",
    "PULocationID", "DOLocationID", "payment_type",
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
    "improvement_surcharge", "total_amount", "congestion_surcharge",
]

TRIP_DTYPES = {
    # passenger_count and RatecodeID can contain nulls in the raw 2019 file,
    # so they're loaded as plain float32 (numpy has no native nullable int)
    # and cast to proper ints later, after clean.py drops/fills the nulls.
    # We deliberately avoid pandas *nullable extension* dtypes (Int8,
    # Float32 capital-F, category) — those use masked-array storage that
    # doesn't bind correctly to sqlite3 at insert time and can trip CHECK
    # constraints. Plain numpy dtypes (float32, int32/64, object) are safe;
    # database/insert.py does a final .astype(object) pass to unwrap numpy
    # scalars to native Python int/float right before binding.
    "VendorID":              "float32",
    "passenger_count":       "float32",
    "trip_distance":         "float32",
    "RatecodeID":            "float32",
    "store_and_fwd_flag":    "object",
    "PULocationID":          "int32",
    "DOLocationID":          "int32",
    "payment_type":          "float32",
    "fare_amount":           "float32",
    "extra":                 "float32",
    "mta_tax":               "float32",
    "tip_amount":            "float32",
    "tolls_amount":          "float32",
    "improvement_surcharge": "float32",
    "total_amount":          "float32",
    "congestion_surcharge":  "float32",
}


def _find_file(candidates: list, label: str) -> Path:
    """Return the first path that exists, or raise a clear error listing all checked paths."""
    for p in candidates:
        if p.exists():
            return p
    searched = "\n  ".join(str(p) for p in candidates)
    if "tripdata" in label:
        hint = (
            "This is the large trip-data CSV (~650MB), which is too big for "
            "GitHub and is hosted externally. Download it using the link in "
            "the README's 'Dataset' section and place it in data/raw/."
        )
    else:
        hint = (
            "This file should already be in the repo under data/raw/. "
            "If it's missing, check that your git clone completed fully."
        )
    raise FileNotFoundError(
        f"\n[data_loader] Could not find {label}.\n"
        f"Searched these locations:\n  {searched}\n\n{hint}"
    )


def load_trips() -> pd.DataFrame:
    """
    Load the yellow taxi trip CSV (January 2019 data).
    Returns raw DataFrame — no cleaning applied here.
    """
    path = _find_file(TRIP_CSV_SEARCH, "yellow_tripdata_2019-01.csv (tripdata)")
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
    """Load the taxi zone lookup CSV. Returns normalised DataFrame."""
    path = _find_file(ZONE_CSV_SEARCH, "taxi_zone_lookup.csv")
    print(f"[data_loader] Loading zone lookup from:\n  {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={"locationid": "zone_id", "zone": "zone_name"}, inplace=True)

    # TLC's lookup includes two special placeholder zones with blank
    # fields: 264 "Unknown" (no zone_name/service_zone) and 265 "Outside
    # of NYC" (no borough/service_zone). Fill them so downstream merges
    # and the zones DB table (NOT NULL columns) don't silently drop them.
    df["zone_name"]    = df["zone_name"].fillna("Unknown")
    df["borough"]      = df["borough"].fillna("Unknown")
    df["service_zone"] = df["service_zone"].fillna("N/A")

    print(f"[data_loader] Loaded {len(df):,} zone records.")
    return df


def load_spatial():
    """
    Load the taxi zones shapefile.
    Requires geopandas — returns None gracefully if not installed or file missing,
    so the rest of the pipeline can continue without spatial data.
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
