"""
run_pipeline.py
===============
Task 1 – Data Processing & Cleaning  (MAIN ENTRY POINT)

Run this FIRST before database/insert.py.

Steps:
  1. Load raw source files
  2. Clean trips data
  3. Engineer derived features
  4. Join zone names onto trips
  5. Export cleaned parquet + zones CSV + cleaning log

Run from the project root:
    python run_pipeline.py        (Windows CMD / PowerShell)
    python3 run_pipeline.py       (macOS / Linux)
"""

from pathlib import Path
import gc

# Output directory — always relative to this file, not the working directory
ROOT       = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("=" * 60)
    print("  NYC TAXI ETL PIPELINE")
    print("=" * 60)

    # ── Step 1: Load ──────────────────────────────────────────────
    from pipeline.data_loader         import load_trips, load_zones, load_spatial
    from pipeline.clean               import clean_trips
    from pipeline.feature_engineering import add_features

    trips   = load_trips()
    zones   = load_zones()
    spatial = load_spatial()   # optional — None if geopandas not installed

    # ── Step 2: Clean ─────────────────────────────────────────────
    cleaned, log = clean_trips(trips)
    log.print_summary()
    log.to_csv(OUTPUT_DIR / "cleaning_log.csv")
    log.to_json(OUTPUT_DIR / "cleaning_log.json")

    # Free the raw 7M+ row frame now that cleaning is done — this dataset
    # is large enough that holding both raw and cleaned versions in memory
    # at once can exhaust RAM on machines with limited memory.
    del trips
    gc.collect()

    # ── Step 3: Feature engineering ───────────────────────────────
    enriched = add_features(cleaned)
    del cleaned
    gc.collect()

    # ── Step 4: Join zone names onto trips ────────────────────────
    # Pickup zone
    pu_zones = zones.rename(columns={
        "zone_id":      "pulocationid",
        "zone_name":    "pu_zone",
        "borough":      "pu_borough",
        "service_zone": "pu_service_zone",
    })
    merged_pu = enriched.merge(pu_zones, on="pulocationid", how="left")
    del enriched, pu_zones
    gc.collect()

    # Dropoff zone
    do_zones = zones.rename(columns={
        "zone_id":      "dolocationid",
        "zone_name":    "do_zone",
        "borough":      "do_borough",
        "service_zone": "do_service_zone",
    })
    enriched = merged_pu.merge(do_zones, on="dolocationid", how="left")
    del merged_pu, do_zones
    gc.collect()

    print(f"\n[pipeline] Enriched shape : {enriched.shape}")

    # ── Step 5: Export ────────────────────────────────────────────
    trips_out = OUTPUT_DIR / "trips_cleaned.parquet"
    enriched.to_parquet(trips_out, index=False)
    print(f"[pipeline] Saved trips    → {trips_out}")

    zones_out = OUTPUT_DIR / "zones_clean.csv"
    zones.to_csv(zones_out, index=False)
    print(f"[pipeline] Saved zones    → {zones_out}")

    # Optional: export GeoJSON if spatial data loaded
    if spatial is not None:
        try:
            # The shapefile has both 'objectid' (1..263 sequential) and
            # 'locationid' (the real TLC zone ID). They happen to align in
            # this dataset, but we merge on locationid since that's the
            # column that's guaranteed to match taxi_zone_lookup.csv.
            id_col = "locationid" if "locationid" in spatial.columns else "objectid"
            merged_geo = spatial.merge(
                zones[["zone_id", "zone_name", "borough", "service_zone"]],
                left_on=id_col, right_on="zone_id", how="left"
            )
            if merged_geo.crs and merged_geo.crs.to_epsg() != 4326:
                merged_geo = merged_geo.to_crs(epsg=4326)
            geo_out = OUTPUT_DIR / "zones_spatial.geojson"
            merged_geo.to_file(geo_out, driver="GeoJSON")
            print(f"[pipeline] Saved GeoJSON  → {geo_out}")
        except Exception as e:
            print(f"[pipeline] GeoJSON export skipped: {e}")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print(f"  Output folder: {OUTPUT_DIR}")
    print("=" * 60)
    print("\nNext step: run  python database/insert.py")
    return enriched, zones


if __name__ == "__main__":
    run()
