"""
app.py
======
Task 3 – Backend API (Flask)
Serves the NYC Taxi Dashboard frontend with JSON data from SQLite/PostgreSQL.

Run:
    pip install flask flask-cors
    python backend/app.py

Endpoints (all return JSON):
    GET /api/kpis
    GET /api/daily-trips
    GET /api/hourly-volume
    GET /api/borough-summary
    GET /api/top-zones?n=10&type=pickup
    GET /api/payment-breakdown
    GET /api/fare-distribution
    GET /api/fare-by-hour
    GET /api/distance-distribution
    GET /api/heatmap
    GET /api/rush-hour-comparison
    GET /api/zones?borough=&service=&search=&page=1&per_page=15
    GET /api/insight/airport
    GET /api/insight/night-efficiency
    GET /api/insight/tips
"""

import os
import sqlite3
import json
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app   = Flask(__name__, static_folder="../front", static_url_path="")
CORS(app, origins="*")

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "nyc_taxi.db"))


# ── DB connection helper ──────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT and return list of dicts."""
    with get_db() as conn:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params: tuple = ()) -> dict | None:
    """Run a SELECT and return first row as dict, or None."""
    rows = query(sql, params)
    return rows[0] if rows else None


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("../front", "index.html")


# ── Overview / KPI ────────────────────────────────────────────────────────────

@app.route("/api/kpis")
def kpis():
    row = query_one("""
        SELECT
            COUNT(*)                              AS total_trips,
            ROUND(AVG(fare_amount), 2)            AS avg_fare,
            ROUND(AVG(trip_distance), 2)          AS avg_distance_mi,
            ROUND(AVG(trip_duration_sec)/60.0, 1) AS avg_duration_min,
            ROUND(AVG(tip_pct), 1)                AS avg_tip_pct,
            ROUND(AVG(total_amount), 2)           AS avg_total_amount,
            ROUND(AVG(speed_mph), 1)              AS avg_speed_mph,
            COUNT(DISTINCT pu_zone_id)            AS active_zones
        FROM trips
    """)
    return jsonify(row)


@app.route("/api/daily-trips")
def daily_trips():
    rows = query("""
        SELECT pickup_date, COUNT(*) AS trips,
               ROUND(AVG(fare_amount),2) AS avg_fare
        FROM trips GROUP BY pickup_date ORDER BY pickup_date
    """)
    return jsonify(rows)


@app.route("/api/hourly-volume")
def hourly_volume():
    rows = query("""
        SELECT pickup_hour AS hour,
               COUNT(*) AS total_trips,
               ROUND(COUNT(*)*1.0/31, 0) AS avg_trips_per_day,
               ROUND(AVG(fare_amount), 2) AS avg_fare,
               ROUND(AVG(speed_mph), 1)   AS avg_speed_mph,
               ROUND(AVG(fare_amount)/NULLIF(AVG(trip_duration_sec)/60.0,0),2)
                                          AS fare_per_minute
        FROM trips GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    return jsonify(rows)


# ── Borough & Zone ────────────────────────────────────────────────────────────

@app.route("/api/borough-summary")
def borough_summary():
    rows = query("""
        SELECT z.borough,
               COUNT(*) AS trips,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM trips),1) AS pct,
               ROUND(AVG(t.fare_amount),2)   AS avg_fare,
               ROUND(AVG(t.trip_distance),2) AS avg_distance,
               ROUND(SUM(t.total_amount),0)  AS total_revenue
        FROM trips t JOIN zones z ON t.pu_zone_id=z.zone_id
        GROUP BY z.borough ORDER BY trips DESC
    """)
    return jsonify(rows)


@app.route("/api/top-zones")
def top_zones():
    n    = min(int(request.args.get("n", 10)), 50)
    kind = request.args.get("type", "pickup")
    zone_col = "pu_zone_id" if kind == "pickup" else "do_zone_id"
    rows = query(f"""
        SELECT z.zone_id, z.zone_name, z.borough, z.service_zone,
               COUNT(*) AS trips,
               ROUND(AVG(t.fare_amount),2) AS avg_fare,
               ROUND(AVG(t.tip_pct),1)    AS avg_tip_pct
        FROM trips t JOIN zones z ON t.{zone_col}=z.zone_id
        GROUP BY z.zone_id ORDER BY trips DESC LIMIT ?
    """, (n,))
    return jsonify(rows)


@app.route("/api/zone-service-summary")
def zone_service_summary():
    rows = query("""
        SELECT z.service_zone,
               COUNT(*) AS trips,
               ROUND(AVG(t.fare_amount),2)    AS avg_fare,
               ROUND(AVG(t.trip_distance),2)  AS avg_distance,
               ROUND(AVG(t.tip_pct),1)        AS avg_tip_pct
        FROM trips t JOIN zones z ON t.pu_zone_id=z.zone_id
        GROUP BY z.service_zone ORDER BY avg_fare DESC
    """)
    return jsonify(rows)


# ── Fare Analysis ─────────────────────────────────────────────────────────────

@app.route("/api/payment-breakdown")
def payment_breakdown():
    rows = query("""
        SELECT payment_type,
               CASE payment_type WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash'
                    WHEN 3 THEN 'No charge' WHEN 4 THEN 'Dispute'
                    ELSE 'Other' END AS label,
               COUNT(*) AS trips,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM trips),1) AS pct,
               ROUND(AVG(fare_amount),2) AS avg_fare,
               ROUND(AVG(tip_pct),1)    AS avg_tip_pct
        FROM trips GROUP BY payment_type ORDER BY trips DESC
    """)
    return jsonify(rows)


@app.route("/api/fare-distribution")
def fare_distribution():
    rows = query("""
        SELECT CASE
               WHEN fare_amount <  5  THEN 'Under $5'
               WHEN fare_amount < 10  THEN '$5–10'
               WHEN fare_amount < 15  THEN '$10–15'
               WHEN fare_amount < 20  THEN '$15–20'
               WHEN fare_amount < 30  THEN '$20–30'
               WHEN fare_amount < 50  THEN '$30–50'
               ELSE '$50+' END AS bucket,
               COUNT(*) AS trips,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM trips),1) AS pct
        FROM trips GROUP BY bucket ORDER BY MIN(fare_amount)
    """)
    return jsonify(rows)


@app.route("/api/fare-by-hour")
def fare_by_hour():
    rows = query("""
        SELECT pickup_hour AS hour,
               ROUND(AVG(fare_amount),2) AS avg_fare,
               ROUND(AVG(fare_per_mile),2) AS avg_fare_per_mile,
               ROUND(AVG(fare_amount)/NULLIF(AVG(trip_duration_sec)/60.0,0),2)
                                          AS fare_per_minute
        FROM trips GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    return jsonify(rows)


# ── Trip Patterns ─────────────────────────────────────────────────────────────

@app.route("/api/distance-distribution")
def distance_distribution():
    rows = query("""
        SELECT CASE
               WHEN trip_distance <  1  THEN '0–1 mi'
               WHEN trip_distance <  2  THEN '1–2 mi'
               WHEN trip_distance <  3  THEN '2–3 mi'
               WHEN trip_distance <  5  THEN '3–5 mi'
               WHEN trip_distance < 10  THEN '5–10 mi'
               WHEN trip_distance < 20  THEN '10–20 mi'
               ELSE '20+ mi' END AS bucket,
               COUNT(*) AS trips,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM trips),1) AS pct
        FROM trips GROUP BY bucket ORDER BY MIN(trip_distance)
    """)
    return jsonify(rows)


@app.route("/api/heatmap")
def heatmap():
    rows = query("""
        SELECT pickup_dow AS day_of_week, pickup_hour AS hour, COUNT(*) AS trips
        FROM trips GROUP BY pickup_dow, pickup_hour
        ORDER BY pickup_dow, pickup_hour
    """)
    return jsonify(rows)


@app.route("/api/rush-hour-comparison")
def rush_hour_comparison():
    rows = query("""
        SELECT is_rush_hour,
               COUNT(*) AS trips,
               ROUND(AVG(fare_amount),2) AS avg_fare,
               ROUND(AVG(speed_mph),1)   AS avg_speed,
               ROUND(AVG(trip_duration_sec)/60.0,1) AS avg_duration_min,
               ROUND(AVG(tip_pct),1)    AS avg_tip_pct
        FROM trips GROUP BY is_rush_hour
    """)
    return jsonify(rows)


# ── Zone Explorer (paginated) ─────────────────────────────────────────────────

@app.route("/api/zones")
def zones():
    borough  = request.args.get("borough", "")
    service  = request.args.get("service", "")
    search   = f"%{request.args.get('search', '')}%"
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(int(request.args.get("per_page", 15)), 100)
    offset   = (page - 1) * per_page

    rows = query("""
        SELECT z.zone_id, z.zone_name, z.borough, z.service_zone,
               COUNT(t.trip_id)            AS total_trips,
               ROUND(AVG(t.fare_amount),2) AS avg_fare
        FROM zones z LEFT JOIN trips t ON z.zone_id = t.pu_zone_id
        WHERE (? = '' OR z.borough      = ?)
          AND (? = '' OR z.service_zone = ?)
          AND z.zone_name LIKE ?
        GROUP BY z.zone_id
        ORDER BY total_trips DESC
        LIMIT ? OFFSET ?
    """, (borough, borough, service, service, search, per_page, offset))

    total = query_one("""
        SELECT COUNT(*) AS n FROM zones z
        WHERE (? = '' OR z.borough      = ?)
          AND (? = '' OR z.service_zone = ?)
          AND z.zone_name LIKE ?
    """, (borough, borough, service, service, search))

    return jsonify({"data": rows, "total": total["n"] if total else 0, "page": page, "per_page": per_page})


# ── Insight endpoints ─────────────────────────────────────────────────────────

@app.route("/api/insight/airport")
def insight_airport():
    rows = query("""
        SELECT z.service_zone,
               COUNT(*) AS trips,
               ROUND(AVG(t.fare_amount),2) AS avg_fare
        FROM trips t JOIN zones z ON t.pu_zone_id=z.zone_id
        GROUP BY z.service_zone ORDER BY avg_fare DESC
    """)
    return jsonify(rows)


@app.route("/api/insight/night-efficiency")
def insight_night():
    rows = query("""
        SELECT pickup_hour AS hour,
               ROUND(AVG(speed_mph),1) AS avg_speed,
               ROUND(AVG(fare_amount)/NULLIF(AVG(trip_duration_sec)/60.0,0),2) AS fare_per_min,
               COUNT(*) AS trips
        FROM trips GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    return jsonify(rows)


@app.route("/api/insight/tips")
def insight_tips():
    rows = query("""
        SELECT payment_type,
               CASE payment_type WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash'
                    WHEN 3 THEN 'No charge' ELSE 'Other' END AS label,
               ROUND(AVG(tip_pct),1)    AS avg_tip_pct,
               ROUND(AVG(tip_amount),2) AS avg_tip_amount,
               COUNT(*) AS trips
        FROM trips GROUP BY payment_type ORDER BY avg_tip_pct DESC
    """)
    return jsonify(rows)


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    try:
        count = query_one("SELECT COUNT(*) AS n FROM trips")
        return jsonify({"status": "ok", "trip_count": count["n"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"[app] Starting NYC Taxi API on http://localhost:{port}")
    print(f"[app] DB: {DB_PATH}")
    app.run(host="0.0.0.0", port=port, debug=debug)
