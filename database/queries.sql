-- OVERVIEW / KPI QUERIES


-- [GET /api/kpis]  Top-level summary statistics
SELECT
    COUNT(*)                          AS total_trips,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(trip_distance), 2)      AS avg_distance_mi,
    ROUND(AVG(trip_duration_sec)/60.0, 1) AS avg_duration_min,
    ROUND(AVG(tip_pct), 1)            AS avg_tip_pct,
    ROUND(AVG(total_amount), 2)       AS avg_total_amount,
    ROUND(AVG(speed_mph), 1)          AS avg_speed_mph
FROM trips;


-- [GET /api/daily-trips]  Trip count per calendar day
SELECT
    pickup_date,
    COUNT(*)                     AS trips,
    ROUND(AVG(fare_amount), 2)   AS avg_fare,
    ROUND(AVG(trip_distance), 2) AS avg_distance
FROM trips
GROUP BY pickup_date
ORDER BY pickup_date;


-- [GET /api/hourly-volume]  Average trips per hour (across all days)
SELECT
    pickup_hour                       AS hour,
    COUNT(*)                          AS total_trips,
    ROUND(COUNT(*) * 1.0 / 31, 0)    AS avg_trips_per_day,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(speed_mph), 1)          AS avg_speed_mph,
    ROUND(AVG(fare_amount) / NULLIF(AVG(trip_duration_sec)/60.0,0), 2)
                                      AS fare_per_minute
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;



-- BOROUGH & ZONE QUERIES


-- [GET /api/borough-summary]  Trips & revenue by pickup borough
SELECT
    z.borough,
    COUNT(*)                          AS trips,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trips), 1) AS pct_of_total,
    ROUND(AVG(t.fare_amount), 2)      AS avg_fare,
    ROUND(AVG(t.trip_distance), 2)    AS avg_distance,
    ROUND(SUM(t.total_amount), 0)     AS total_revenue
FROM trips t
JOIN zones z ON t.pu_zone_id = z.zone_id
GROUP BY z.borough
ORDER BY trips DESC;


-- [GET /api/top-zones?n=10&type=pickup]  Top N pickup zones
SELECT
    z.zone_id,
    z.zone_name,
    z.borough,
    z.service_zone,
    COUNT(*)                          AS trips,
    ROUND(AVG(t.fare_amount), 2)      AS avg_fare,
    ROUND(AVG(t.tip_pct), 1)         AS avg_tip_pct
FROM trips t
JOIN zones z ON t.pu_zone_id = z.zone_id
GROUP BY z.zone_id
ORDER BY trips DESC
LIMIT 10;


-- [GET /api/top-zones?type=dropoff]  Top N dropoff zones
SELECT
    z.zone_id,
    z.zone_name,
    z.borough,
    z.service_zone,
    COUNT(*) AS trips
FROM trips t
JOIN zones z ON t.do_zone_id = z.zone_id
GROUP BY z.zone_id
ORDER BY trips DESC
LIMIT 10;


-- [GET /api/zone-service-summary]  Avg fare by service zone type
SELECT
    z.service_zone,
    COUNT(*)                          AS trips,
    ROUND(AVG(t.fare_amount), 2)      AS avg_fare,
    ROUND(AVG(t.trip_distance), 2)    AS avg_distance,
    ROUND(AVG(t.tip_pct), 1)         AS avg_tip_pct
FROM trips t
JOIN zones z ON t.pu_zone_id = z.zone_id
GROUP BY z.service_zone
ORDER BY avg_fare DESC;



-- FARE ANALYSIS QUERIES


-- [GET /api/payment-breakdown]  Trips & tips by payment type
SELECT
    payment_type,
    CASE payment_type
        WHEN 1 THEN 'Credit card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'Unknown'
        WHEN 6 THEN 'Voided'
        ELSE 'Other'
    END                               AS payment_label,
    COUNT(*)                          AS trips,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trips), 1) AS pct,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(tip_amount), 2)         AS avg_tip,
    ROUND(AVG(tip_pct), 1)           AS avg_tip_pct
FROM trips
GROUP BY payment_type
ORDER BY trips DESC;


-- [GET /api/fare-distribution]  Fare amount histogram buckets
SELECT
    CASE
        WHEN fare_amount <  5  THEN 'Under $5'
        WHEN fare_amount < 10  THEN '$5–10'
        WHEN fare_amount < 15  THEN '$10–15'
        WHEN fare_amount < 20  THEN '$15–20'
        WHEN fare_amount < 30  THEN '$20–30'
        WHEN fare_amount < 50  THEN '$30–50'
        ELSE '$50+'
    END                               AS bucket,
    COUNT(*)                          AS trips,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trips), 1) AS pct
FROM trips
GROUP BY bucket
ORDER BY MIN(fare_amount);


-- [GET /api/fare-by-hour]  Avg fare and fare/minute by hour
SELECT
    pickup_hour                       AS hour,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(fare_per_mile), 2)      AS avg_fare_per_mile,
    ROUND(AVG(fare_amount) / NULLIF(AVG(trip_duration_sec)/60.0, 0), 2)
                                      AS fare_per_minute
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;


-- TRIP PATTERN QUERIES


-- [GET /api/distance-distribution]
SELECT
    CASE
        WHEN trip_distance <  1  THEN '0–1 mi'
        WHEN trip_distance <  2  THEN '1–2 mi'
        WHEN trip_distance <  3  THEN '2–3 mi'
        WHEN trip_distance <  5  THEN '3–5 mi'
        WHEN trip_distance < 10  THEN '5–10 mi'
        WHEN trip_distance < 20  THEN '10–20 mi'
        ELSE '20+ mi'
    END                               AS bucket,
    COUNT(*)                          AS trips,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trips), 1) AS pct
FROM trips
GROUP BY bucket
ORDER BY MIN(trip_distance);


-- [GET /api/heatmap]  Avg trips by day-of-week × hour
SELECT
    pickup_dow   AS day_of_week,   -- 0=Mon … 6=Sun
    pickup_hour  AS hour,
    COUNT(*)     AS trips
FROM trips
GROUP BY pickup_dow, pickup_hour
ORDER BY pickup_dow, pickup_hour;


-- [GET /api/rush-hour-comparison]  Rush vs non-rush metrics
SELECT
    is_rush_hour,
    COUNT(*)                          AS trips,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(speed_mph), 1)          AS avg_speed,
    ROUND(AVG(trip_duration_sec)/60.0,1) AS avg_duration_min,
    ROUND(AVG(tip_pct), 1)           AS avg_tip_pct
FROM trips
GROUP BY is_rush_hour;

-- INSIGHT QUERIES (used in Insights page)


-- Insight 1: Airport vs city fare comparison
SELECT
    is_airport_trip,
    COUNT(*)                          AS trips,
    ROUND(AVG(fare_amount), 2)        AS avg_fare,
    ROUND(AVG(trip_distance), 2)      AS avg_distance,
    ROUND(AVG(tip_pct), 1)           AS avg_tip_pct
FROM trips
GROUP BY is_airport_trip;


-- Insight 2: Speed & fare efficiency by hour (night vs day)
SELECT
    pickup_hour,
    ROUND(AVG(speed_mph), 1)          AS avg_speed_mph,
    ROUND(AVG(fare_amount) / NULLIF(AVG(trip_duration_sec)/60.0,0), 2)
                                      AS fare_per_min,
    COUNT(*)                          AS trips
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;


-- Insight 3: Tip behaviour by payment type
SELECT
    payment_type,
    CASE payment_type WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash'
                      WHEN 3 THEN 'No charge'   ELSE 'Other' END AS label,
    ROUND(AVG(tip_pct), 1)  AS avg_tip_pct,
    ROUND(AVG(tip_amount),2) AS avg_tip_amount,
    COUNT(*)                AS trips
FROM trips
GROUP BY payment_type
ORDER BY avg_tip_pct DESC;



-- ZONE EXPLORER (filterable, paginated)


-- [GET /api/zones?borough=Manhattan&service=Yellow+Zone&page=1]
-- Replace :borough, :service, :limit, :offset with parameters
SELECT
    z.zone_id,
    z.zone_name,
    z.borough,
    z.service_zone,
    COUNT(t.trip_id)             AS total_trips,
    ROUND(AVG(t.fare_amount),2)  AS avg_fare
FROM zones z
LEFT JOIN trips t ON z.zone_id = t.pu_zone_id
WHERE
    (:borough  = '' OR z.borough      = :borough)  AND
    (:service  = '' OR z.service_zone = :service)
GROUP BY z.zone_id
ORDER BY total_trips DESC
LIMIT  :limit
OFFSET :offset;
