"""
run_pipeline.py
===============
Task 1 – Data Processing & Cleaning  (MAIN ENTRY POINT)

Runs the full ETL pipeline:
  1. Load raw source files
  2. Clean trips data
  3. Engineer derived features
  4. Integrate zone lookup
  5. Export cleaned parquet + cleaning log CSV

Run:
    python run_pipeline.py
"""

from pathlib import Path
from pipeline.data_loader        import load_all
from pipeline.clean              import clean_trips
from pipeline.feature_engineering import add_features

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("=" * 60)
    print("  NYC TAXI ETL PIPELINE")
    print("=" * 60)

    # ── Step 1: Load ──────────────────────────────────────────────
    trips, zones, spatial = load_all()

    # ── Step 2: Clean ─────────────────────────────────────────────
    cleaned, log = clean_trips(trips)
    log.print_summary()
    log.to_csv(OUTPUT_DIR / "cleaning_log.csv")
    log.to_json(OUTPUT_DIR / "cleaning_log.json")

    # ── Step 3: Feature engineering ───────────────────────────────
    enriched = add_features(cleaned)

    # ── Step 4: Join zone names ───────────────────────────────────
    # Pickup zone
    enriched = enriched.merge(
        zones.rename(columns={"zone_id":"pulocationid",
                               "zone_name":"pu_zone","borough":"pu_borough",
                               "service_zone":"pu_service_zone"}),
        on="pulocationid", how="left"
    )
    # Dropoff zone
    enriched = enriched.merge(
        zones.rename(columns={"zone_id":"dolocationid",
                               "zone_name":"do_zone","borough":"do_borough",
                               "service_zone":"do_service_zone"}),
        on="dolocationid", how="left"
    )

    print(f"\n[pipeline] Final enriched shape: {enriched.shape}")
    print(f"[pipeline] Columns: {list(enriched.columns)}")

    # ── Step 5: Export ────────────────────────────────────────────
    out_path = OUTPUT_DIR / "trips_cleaned.parquet"
    enriched.to_parquet(out_path, index=False)
    print(f"\n[pipeline] Saved cleaned data → {out_path}")

    # Also save zone lookup (normalised) for DB insert
    zones.to_csv(OUTPUT_DIR / "zones_clean.csv", index=False)
    print(f"[pipeline] Saved zone lookup  → {OUTPUT_DIR / 'zones_clean.csv'}")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    return enriched, zones


if __name__ == "__main__":
    run()
