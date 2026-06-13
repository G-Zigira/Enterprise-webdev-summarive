"""
integrate.py
============
Task 1 – Data Processing & Cleaning
Step 4: Spatially join taxi_zones shapefile with taxi_zone_lookup.csv.

Produces a unified GeoDataFrame that links:
  - Zone polygons (geometry) from taxi_zones.shp
  - Borough + service zone names from taxi_zone_lookup.csv

The output is exported as:
  - data/processed/zones_spatial.geojson  (for mapping in a frontend map library)
  - data/processed/zones_clean.csv        (flat lookup for DB insert)

Usage:
    python -m pipeline.integrate
    # or import and call integrate() from run_pipeline.py
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path

ROOT          = Path(__file__).resolve().parent.parent
SHAPEFILE     = ROOT / "data" / "raw" / "taxi_zones" / "taxi_zones.shp"
ZONE_CSV      = ROOT / "data" / "raw" / "taxi_zone_lookup.csv"
OUTPUT_DIR    = ROOT / "data" / "processed"


def integrate(
    shp_path: Path = SHAPEFILE,
    csv_path: Path = ZONE_CSV,
    output_dir: Path = OUTPUT_DIR,
) -> gpd.GeoDataFrame:
    """
    Join shapefile geometry with zone lookup CSV.

    Returns
    -------
    gdf : GeoDataFrame with columns:
          zone_id, zone_name, borough, service_zone, geometry
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load shapefile ────────────────────────────────────────────────────
    print(f"[integrate] Reading shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)
    gdf.columns = [c.strip().lower() for c in gdf.columns]

    # The shapefile uses 'locationid' or 'objectid' as zone key
    # Rename to zone_id for consistency
    id_col = next((c for c in gdf.columns if 'locationid' in c or 'objectid' in c), None)
    if id_col:
        gdf.rename(columns={id_col: 'zone_id'}, inplace=True)

    # Keep only geometry + zone_id
    gdf = gdf[['zone_id', 'geometry']].copy()

    # ── Load zone lookup CSV ──────────────────────────────────────────────
    print(f"[integrate] Reading zone CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={
        'locationid': 'zone_id',
        'zone':       'zone_name',
    }, inplace=True, errors='ignore')
    df['zone_id'] = df['zone_id'].astype(int)

    # ── Merge ─────────────────────────────────────────────────────────────
    print("[integrate] Merging shapefile with zone lookup …")
    merged = gdf.merge(df, on='zone_id', how='left')

    # Check for unmatched rows
    unmatched = merged[merged['zone_name'].isna()]
    if len(unmatched):
        print(f"[integrate] WARNING: {len(unmatched)} zones have no CSV match: "
              f"{unmatched['zone_id'].tolist()}")

    # ── Reproject to WGS84 (EPSG:4326) for GeoJSON / web maps ────────────
    if merged.crs is not None and merged.crs.to_epsg() != 4326:
        print(f"[integrate] Reprojecting from {merged.crs} → EPSG:4326 …")
        merged = merged.to_crs(epsg=4326)

    # ── Export GeoJSON ────────────────────────────────────────────────────
    geojson_path = output_dir / "zones_spatial.geojson"
    merged.to_file(geojson_path, driver='GeoJSON')
    print(f"[integrate] Saved GeoJSON → {geojson_path}")

    # ── Export flat CSV (for DB insert) ───────────────────────────────────
    csv_out = output_dir / "zones_clean.csv"
    merged[['zone_id', 'zone_name', 'borough', 'service_zone']].to_csv(csv_out, index=False)
    print(f"[integrate] Saved CSV     → {csv_out}")

    print(f"[integrate] Done. {len(merged):,} zones integrated.")
    return merged


if __name__ == "__main__":
    gdf = integrate()
    print("\nSample output:")
    print(gdf[['zone_id', 'zone_name', 'borough', 'service_zone']].head(10).to_string(index=False))
