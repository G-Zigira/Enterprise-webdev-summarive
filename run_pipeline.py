
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

    # Step 1: Load 
    trips, zones, spatial = load_all()

    # Step 2: Clean 
    cleaned, log = clean_trips(trips)
    log.print_summary()
    log.to_csv(OUTPUT_DIR / "cleaning_log.csv")
    log.to_json(OUTPUT_DIR / "cleaning_log.json")

    # Step 3: Feature engineering 
    enriched = add_features(cleaned)
    del cleaned
    gc.collect()

    # Step 4: Join zone names
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

    # Step 5: Export 
    out_path = OUTPUT_DIR / "trips_cleaned.parquet"
    enriched.to_parquet(out_path, index=False)
    print(f"\n[pipeline] Saved cleaned data → {out_path}")

    # Also save zone lookup (normalised) for DB insert
    zones.to_csv(OUTPUT_DIR / "zones_clean.csv", index=False)
    print(f"[pipeline] Saved zone lookup  → {OUTPUT_DIR / 'zones_clean.csv'}")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print(f"  Output folder: {OUTPUT_DIR}")
    print("=" * 60)
    print("\nNext step: run  python database/insert.py")
    return enriched, zones


if __name__ == "__main__":
    run()
