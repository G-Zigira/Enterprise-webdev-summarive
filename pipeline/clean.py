import pandas as pd
import numpy as np
from pipeline.cleaning_log import CleaningLog


# Constants (physical/logical bounds) 
MIN_FARE        = 2.50      
MAX_FARE        = 500.00    
MIN_DISTANCE    = 0.01     
MAX_DISTANCE    = 150.0    
MIN_DURATION    = 60       
MAX_DURATION    = 10_800    
MIN_PASSENGERS  = 1
MAX_PASSENGERS  = 6         
VALID_PAYMENT   = {1, 2, 3, 4, 5, 6}
VALID_RATE_CODE = {1, 2, 3, 4, 5, 6}
DATE_START      = "2019-01-01"
DATE_END        = "2019-01-31 23:59:59"


def clean_trips(df: pd.DataFrame, log: CleaningLog | None = None) -> tuple[pd.DataFrame, CleaningLog]:
    """
    Apply all cleaning rules to the raw trips DataFrame.

    Parameters
    ----------
    df  : raw trip DataFrame from data_loader.load_trips()
    log : optional CleaningLog to accumulate stats; one is created if None

    Returns
    -------
    cleaned : cleaned DataFrame
    log     : CleaningLog with all exclusion counts
    """
    if log is None:
        log = CleaningLog()

    original_len = len(df)
    log.record("original_count", original_len, "Raw records loaded")

    # 1. Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    #  2. Drop exact duplicates
    before = len(df)
    df.drop_duplicates(inplace=True)
    dropped = before - len(df)
    log.record("duplicates_removed", dropped, "Exact duplicate rows")

    # 3. Drop rows with null critical fields
    critical = [
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "pulocationid", "dolocationid",
        "trip_distance", "fare_amount"
    ]
    before = len(df)
    df.dropna(subset=critical, inplace=True)
    log.record("nulls_critical", before - len(df), "Null in critical fields")

    # 4. Parse & validate timestamps 
    df["tpep_pickup_datetime"]  = pd.to_datetime(df["tpep_pickup_datetime"],  errors="coerce")
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"], errors="coerce")

    before = len(df)
    df.dropna(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime"], inplace=True)
    log.record("unparseable_timestamps", before - len(df), "Timestamps that could not be parsed")

    # Trips must fall within the dataset month
    mask_date = (
        (df["tpep_pickup_datetime"]  >= DATE_START) &
        (df["tpep_pickup_datetime"]  <= DATE_END)   &
        (df["tpep_dropoff_datetime"] >= DATE_START) &
        (df["tpep_dropoff_datetime"] <= DATE_END)
    )
    before = len(df)
    df = df[mask_date]
    log.record("out_of_range_dates", before - len(df), "Trips outside Jan 2019 window")

    # Dropoff must be after pickup
    before = len(df)
    df = df[df["tpep_dropoff_datetime"] > df["tpep_pickup_datetime"]]
    log.record("negative_duration", before - len(df), "Dropoff before or equal to pickup")

    # 5. Compute trip duration (seconds) for bound checks
    df["trip_duration_sec"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds().astype(int)

    before = len(df)
    df = df[(df["trip_duration_sec"] >= MIN_DURATION) & (df["trip_duration_sec"] <= MAX_DURATION)]
    log.record("duration_outliers", before - len(df), f"Duration outside [{MIN_DURATION}s, {MAX_DURATION}s]")

    # 6. Fare amount bounds
    before = len(df)
    df = df[(df["fare_amount"] >= MIN_FARE) & (df["fare_amount"] <= MAX_FARE)]
    log.record("fare_outliers", before - len(df), f"Fare outside [${MIN_FARE}, ${MAX_FARE}]")

    # 7. Trip distance bounds 
    before = len(df)
    df = df[(df["trip_distance"] >= MIN_DISTANCE) & (df["trip_distance"] <= MAX_DISTANCE)]
    log.record("distance_outliers", before - len(df), f"Distance outside [{MIN_DISTANCE}, {MAX_DISTANCE}] mi")

    # 8. Passenger count 
    before = len(df)
    df["passenger_count"] = df["passenger_count"].fillna(1).astype(int)
    df = df[(df["passenger_count"] >= MIN_PASSENGERS) & (df["passenger_count"] <= MAX_PASSENGERS)]
    log.record("passenger_outliers", before - len(df), f"Passengers outside [{MIN_PASSENGERS}, {MAX_PASSENGERS}]")

    # 9. Validate categorical codes 
    if "payment_type" in df.columns:
        before = len(df)
        df = df[df["payment_type"].isin(VALID_PAYMENT)]
        df["payment_type"] = df["payment_type"].astype(int)
        log.record("invalid_payment_type", before - len(df), "Unknown payment_type codes")

    if "ratecodeid" in df.columns:
        before = len(df)
        df = df[df["ratecodeid"].isin(VALID_RATE_CODE)]
        df["ratecodeid"] = df["ratecodeid"].astype(int)
        log.record("invalid_rate_code", before - len(df), "Unknown ratecodeid codes")


    if "vendorid" in df.columns:
        df["vendorid"] = df["vendorid"].astype(int)
    if "pulocationid" in df.columns:
        df["pulocationid"] = df["pulocationid"].astype(int)
    if "dolocationid" in df.columns:
        df["dolocationid"] = df["dolocationid"].astype(int)

    # 10. Fill remaining non-critical nulls
    if "tip_amount"   in df.columns: df["tip_amount"]   = df["tip_amount"].fillna(0.0)
    if "tolls_amount" in df.columns: df["tolls_amount"] = df["tolls_amount"].fillna(0.0)
    if "mta_tax"      in df.columns: df["mta_tax"]      = df["mta_tax"].fillna(0.5)
    if "improvement_surcharge" in df.columns:
        df["improvement_surcharge"] = df["improvement_surcharge"].fillna(0.3)
    if "congestion_surcharge" in df.columns:
        df["congestion_surcharge"] = df["congestion_surcharge"].fillna(0.0)

    # 11. Reset index 
    df.reset_index(drop=True, inplace=True)

    retained = len(df)
    excluded = original_len - retained
    log.record("final_count",    retained, "Records after all cleaning steps")
    log.record("total_excluded", excluded, f"Total excluded ({excluded/original_len*100:.1f}% of raw data)")

    print(f"[clean] Finished. Retained {retained:,} / {original_len:,} records "
          f"({retained/original_len*100:.1f}%).")
    return df, log


if __name__ == "__main__":
    from pipeline.data_loader import load_trips
    raw = load_trips()
    cleaned, log = clean_trips(raw)
    log.print_summary()
    print(cleaned.dtypes)
