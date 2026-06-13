-- =============================================================
-- schema.sql
-- Task 2 – Database Design & Implementation
-- 
-- Normalized relational schema for the NYC Yellow Taxi dataset.
-- Compatible with PostgreSQL and SQLite (minor dialect notes below).
--
-- Tables
--   rate_codes   – dimension: maps rate_code_id to description
--   zones        – dimension: borough & service zone per location ID
--   trips        – fact: one row per cleaned trip record
--
-- Run: psql -U <user> -d nyc_taxi -f schema.sql
--      OR: sqlite3 nyc_taxi.db < schema.sql
-- =============================================================

PRAGMA foreign_keys = ON;   -- SQLite only; remove for PostgreSQL


-- ── Drop in reverse dependency order ────────────────────────────────────────
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS zones;
DROP TABLE IF EXISTS rate_codes;


-- ── Dimension: rate_codes ────────────────────────────────────────────────────
-- Stores the six TLC rate code categories.
-- Kept separate to avoid string repetition across 3M+ trip rows.
CREATE TABLE rate_codes (
    rate_code_id  INTEGER     PRIMARY KEY,
    description   VARCHAR(50) NOT NULL
);

INSERT INTO rate_codes VALUES
    (1, 'Standard rate'),
    (2, 'JFK'),
    (3, 'Newark'),
    (4, 'Nassau or Westchester'),
    (5, 'Negotiated fare'),
    (6, 'Group ride');


-- ── Dimension: zones ─────────────────────────────────────────────────────────
-- One row per TLC taxi zone (263 zones + 2 special rows).
-- Sourced from taxi_zone_lookup.csv.
CREATE TABLE zones (
    zone_id      INTEGER     PRIMARY KEY,
    zone_name    VARCHAR(100) NOT NULL,
    borough      VARCHAR(50)  NOT NULL,
    service_zone VARCHAR(50)  NOT NULL
);

-- Index: borough filters are common in the dashboard
CREATE INDEX idx_zones_borough ON zones(borough);
CREATE INDEX idx_zones_service ON zones(service_zone);


-- ── Fact: trips ───────────────────────────────────────────────────────────────
-- One row per cleaned trip record from yellow_tripdata_2024-01.parquet.
-- Foreign keys enforce referential integrity with dimension tables.
CREATE TABLE trips (
    trip_id            INTEGER     PRIMARY KEY AUTOINCREMENT,   -- surrogate key
                                   -- PostgreSQL: use SERIAL or BIGSERIAL

    -- Timestamps
    pickup_datetime    TIMESTAMP   NOT NULL,
    dropoff_datetime   TIMESTAMP   NOT NULL,

    -- Dimensions (foreign keys)
    pu_zone_id         INTEGER     NOT NULL REFERENCES zones(zone_id),
    do_zone_id         INTEGER     NOT NULL REFERENCES zones(zone_id),
    rate_code_id       INTEGER     NOT NULL REFERENCES rate_codes(rate_code_id),

    -- Raw trip fields
    passenger_count    SMALLINT    NOT NULL DEFAULT 1,
    trip_distance      DECIMAL(6,2) NOT NULL,
    store_fwd_flag     CHAR(1),            -- 'Y' = stored & forwarded

    -- Fare components
    fare_amount        DECIMAL(8,2) NOT NULL,
    extra              DECIMAL(6,2) NOT NULL DEFAULT 0,
    mta_tax            DECIMAL(6,2) NOT NULL DEFAULT 0.5,
    tip_amount         DECIMAL(8,2) NOT NULL DEFAULT 0,
    tolls_amount       DECIMAL(8,2) NOT NULL DEFAULT 0,
    improvement_surcharge DECIMAL(6,2) NOT NULL DEFAULT 0.3,
    total_amount       DECIMAL(8,2) NOT NULL,
    congestion_surcharge  DECIMAL(6,2),
    airport_fee        DECIMAL(6,2),

    -- Payment
    payment_type       SMALLINT    NOT NULL,   -- 1=CC 2=Cash 3=NoCharge 4=Dispute

    -- ── Derived / engineered features ─────────────────────────────────────
    trip_duration_sec  INTEGER     NOT NULL,           -- Feature 1
    speed_mph          DECIMAL(5,2),                   -- Feature 2
    tip_pct            DECIMAL(5,2) NOT NULL DEFAULT 0, -- Feature 3
    is_rush_hour       SMALLINT    NOT NULL DEFAULT 0,  -- Feature 4 (0/1)
    time_of_day        VARCHAR(12),                    -- Feature 5 (Morning/…)
    fare_per_mile      DECIMAL(6,2),                   -- Feature 6
    is_airport_trip    SMALLINT    NOT NULL DEFAULT 0,  -- Feature 7 (0/1)

    -- Convenience
    pickup_hour        SMALLINT,
    pickup_dow         SMALLINT,   -- 0=Monday … 6=Sunday
    pickup_date        DATE,

    -- Constraints
    CONSTRAINT chk_fare       CHECK (fare_amount   >= 0),
    CONSTRAINT chk_distance   CHECK (trip_distance >= 0),
    CONSTRAINT chk_duration   CHECK (trip_duration_sec > 0),
    CONSTRAINT chk_payment    CHECK (payment_type  BETWEEN 1 AND 6),
    CONSTRAINT chk_passengers CHECK (passenger_count BETWEEN 1 AND 6),
    CONSTRAINT chk_speed      CHECK (speed_mph IS NULL OR speed_mph BETWEEN 0 AND 80),
    CONSTRAINT chk_tip_pct    CHECK (tip_pct >= 0)
);


-- ── Performance indexes (trips fact table) ───────────────────────────────────
-- Chosen based on the most common dashboard filter/aggregate patterns.

-- Time-series queries (daily/hourly aggregations)
CREATE INDEX idx_trips_pickup_dt   ON trips(pickup_datetime);
CREATE INDEX idx_trips_pickup_date ON trips(pickup_date);
CREATE INDEX idx_trips_pickup_hour ON trips(pickup_hour);

-- Zone-based queries (top zones, corridor analysis)
CREATE INDEX idx_trips_pu_zone     ON trips(pu_zone_id);
CREATE INDEX idx_trips_do_zone     ON trips(do_zone_id);

-- Composite: zone + time (most common dashboard combo)
CREATE INDEX idx_trips_pu_zone_date ON trips(pu_zone_id, pickup_date);

-- Filter queries
CREATE INDEX idx_trips_payment     ON trips(payment_type);
CREATE INDEX idx_trips_rush        ON trips(is_rush_hour);
CREATE INDEX idx_trips_airport     ON trips(is_airport_trip);
CREATE INDEX idx_trips_rate_code   ON trips(rate_code_id);


-- =============================================================
-- SAMPLE ANALYTICAL QUERIES (documented here for reference)
-- Full query library is in queries.sql
-- =============================================================

-- Daily trip count
-- SELECT pickup_date, COUNT(*) AS trips
-- FROM trips GROUP BY pickup_date ORDER BY pickup_date;

-- Top 10 pickup zones
-- SELECT z.zone_name, z.borough, COUNT(*) AS trips
-- FROM trips t JOIN zones z ON t.pu_zone_id = z.zone_id
-- GROUP BY z.zone_id ORDER BY trips DESC LIMIT 10;

-- Avg fare by payment type
-- SELECT payment_type, AVG(fare_amount) AS avg_fare,
--        AVG(tip_pct) AS avg_tip_pct
-- FROM trips GROUP BY payment_type;
