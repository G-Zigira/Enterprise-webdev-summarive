# TaxiIQ — NYC Yellow Taxi Analytics Platform

A full-stack enterprise analytics dashboard built on the NYC TLC Yellow Taxi dataset (January 2024).  
Covers three layers: **data pipeline**, **relational database**, and **interactive frontend dashboard**.

---

## Video Walkthrough

> 📹 [Link to video walkthrough — insert your URL here]

---

## Project Structure

```
nyc-taxi-dashboard/
│
├── pipeline/                   # Task 1 — Data Processing & Cleaning
│   ├── data_loader.py          # Load parquet, CSV, shapefile
│   ├── clean.py                # Remove nulls, duplicates, outliers
│   ├── feature_engineering.py  # 7 derived features
│   ├── integrate.py            # Join shapefile + zone lookup → GeoJSON
│   └── cleaning_log.py         # Audit trail of all exclusions
│
├── database/                   # Task 2 — Database Design & Implementation
│   ├── schema.sql              # Normalised schema (trips, zones, rate_codes)
│   ├── insert.py               # Batch-insert cleaned data into DB
│   └── queries.sql             # Full analytical query library
│
├── backend/                    # Task 3 (Backend) — Flask REST API
│   └── app.py                  # 15 JSON endpoints serving the dashboard
│
├── frontend/                   # Task 3 (Frontend) — Dashboard UI
│   ├── index.html              # Single-page shell
│   ├── css/
│   │   ├── theme.css           # Light / dark CSS variables
│   │   └── style.css           # Full component + layout system
│   └── js/
│       ├── data.js             # Simulated data layer (mirrors API)
│       ├── charts.js           # Chart.js wrapper utilities
│       ├── zones.js            # Zone explorer (filter + paginate)
│       ├── algo.js             # Manual max-heap algorithm (live demo)
│       └── main.js             # Page router + all page HTML builders
│
├── data/
│   ├── raw/                    # Place downloaded source files here
│   └── processed/              # Pipeline output (auto-generated)
│
├── run_pipeline.py             # Task 1 entry point — runs full ETL
├── requirements.txt
├── .env.example
└── README.md
```

---

## Dataset Sources

Download from [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page):

| File | Description | Place in |
|------|-------------|----------|
| `yellow_tripdata_2024-01.parquet` | Fact table — trip records | `data/raw/` |
| `taxi_zone_lookup.csv` | Dimension — zone names/boroughs | `data/raw/` |
| `taxi_zones.shp` (+ `.dbf`, `.shx`, `.prj`) | Spatial — zone polygons | `data/raw/taxi_zones/` |

---

## Setup & Installation

### 1. Clone / unzip the project

```bash
cd nyc-taxi-dashboard
```

### 2. Create a Python virtual environment

```bash
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if you want PostgreSQL instead of SQLite
```

---

## Running the Project

### Step 1 — Run the data pipeline (Task 1)

```bash
python run_pipeline.py
```

This will:
- Load `yellow_tripdata_2024-01.parquet` and both dimension files
- Clean the data (remove nulls, duplicates, outliers)
- Engineer 7 derived features
- Join zone lookup with shapefile
- Output cleaned data to `data/processed/`
- Save a `cleaning_log.csv` audit trail

### Step 2 — Set up the database (Task 2)

```bash
python database/insert.py
```

This will:
- Create `nyc_taxi.db` (SQLite) in the project root
- Apply `schema.sql` (3 tables, 12 indexes)
- Insert zone dimension data
- Batch-insert all cleaned trip records

### Step 3 — Start the backend API (Task 3)

```bash
python backend/app.py
```

API runs at `http://localhost:5000`  
Health check: `http://localhost:5000/api/health`

### Step 4 — Open the frontend dashboard

**Option A — With Flask backend (live data):**  
Visit `http://localhost:5000` — Flask serves `frontend/index.html` automatically.

**Option B — Standalone (simulated data, no backend needed):**  
Open `frontend/index.html` directly in your browser. The `data.js` module provides realistic simulated data so all charts and pages work without a running server.

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | KPI cards, daily trip trend, borough breakdown, hourly volume |
| **Trip Patterns** | Distance/duration histograms, day×hour heatmap, top pickup zones |
| **Fare Analysis** | Payment breakdown, fare distribution, fare by hour, tip rates |
| **Zone Explorer** | Filterable, searchable, paginated table of all 263 NYC taxi zones |
| **DB Schema** | ER diagram, schema tables, derived feature SQL |
| **Algorithm** | Manual max-heap implementation with live interactive demo |
| **Key Insights** | 3 data-driven findings with supporting charts |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + trip count |
| GET | `/api/kpis` | Top-level summary statistics |
| GET | `/api/daily-trips` | Trip count per day |
| GET | `/api/hourly-volume` | Avg trips + fare by hour |
| GET | `/api/borough-summary` | Trips & revenue by borough |
| GET | `/api/top-zones?n=10&type=pickup` | Top N zones |
| GET | `/api/payment-breakdown` | Trips by payment type |
| GET | `/api/fare-distribution` | Fare histogram buckets |
| GET | `/api/fare-by-hour` | Avg fare per hour |
| GET | `/api/distance-distribution` | Distance histogram |
| GET | `/api/heatmap` | Trips by day-of-week × hour |
| GET | `/api/rush-hour-comparison` | Rush vs non-rush metrics |
| GET | `/api/zones` | Paginated zone explorer |
| GET | `/api/insight/airport` | Insight 1 data |
| GET | `/api/insight/night-efficiency` | Insight 2 data |
| GET | `/api/insight/tips` | Insight 3 data |

---

## Key Design Decisions

### Why SQLite (default)?
Zero setup — runs immediately without a database server. The schema is fully PostgreSQL-compatible; switching is one line in `.env`.

### Why Flask?
Lightweight, beginner-friendly, and perfectly suited to a read-heavy analytics API. No ORM overhead needed since all queries are pre-written SQL.

### Why vanilla HTML/CSS/JS (no React/Vue)?
The assignment specifies HTML, CSS, and JavaScript. The dashboard uses a module pattern (`CHARTS`, `DATA`, `ALGO`, `ZONES_MODULE`) to keep code organised without a framework.

### Schema normalisation
The `zones` and `rate_codes` dimension tables avoid repeating strings across 3M trip rows — saving ~40% storage and enabling fast `JOIN`-based borough/service-zone filters.

### Custom algorithm
The max-heap in `algo.js` and `database/insert.py` uses no built-in `sort()`, `heapq`, or `Counter`. It's implemented from scratch to satisfy the algorithmic data structure requirement.

---

## Data Cleaning Summary

| Step | Records removed | Reason |
|------|----------------|--------|
| Duplicates | ~1,200 | Exact duplicate rows |
| Null critical fields | ~8,400 | Missing datetime/location/fare |
| Out-of-range dates | ~3,100 | Outside January 2024 |
| Negative duration | ~400 | Dropoff before pickup |
| Duration outliers | ~6,800 | Under 60s or over 3 hours |
| Fare outliers | ~2,900 | Below $2.50 or above $500 |
| Distance outliers | ~1,100 | Below 0.01mi or above 150mi |
| Passenger outliers | ~500 | Outside 1–6 range |

Full audit trail saved to `data/processed/cleaning_log.csv`.

---

## Derived Features

| Feature | Formula | Insight |
|---------|---------|---------|
| `trip_duration_sec` | `dropoff - pickup` (seconds) | Base time metric |
| `speed_mph` | `distance / (duration/3600)` | Traffic congestion proxy |
| `tip_pct` | `tip / fare × 100` | Normalised tipping behaviour |
| `is_rush_hour` | Weekday 7–9am or 5–7pm flag | Demand modelling |
| `time_of_day` | Morning/Afternoon/Evening/Night | Coarse time bucket |
| `fare_per_mile` | `fare / distance` | Price efficiency metric |
| `is_airport_trip` | Zone ID ∈ {1, 132, 138} | High-value segment flag |

---

## Team Participation

> Fill in your team details here per the assignment rubric.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data pipeline | Python, pandas, geopandas, pyarrow |
| Database | SQLite (default) / PostgreSQL |
| Backend API | Flask, flask-cors |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Charts | Chart.js 4.4 |
| Icons | Tabler Icons |
| Fonts | Inter, JetBrains Mono |
