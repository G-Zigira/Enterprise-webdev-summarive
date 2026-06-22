# TaxiIQ — NYC Yellow Taxi Analytics Platform

A full-stack enterprise analytics dashboard built on the NYC TLC Yellow Taxi dataset.
Covers three layers: **data pipeline**, **relational database**, and **interactive frontend dashboard**.

> **Note on the data file name:** the trip data file is named
> `yellow_tripdata_2019-01.csv` and contains January 2019 NYC Yellow Taxi
> trip records. All cleaning, validation, and feature engineering in this
> project is built around this date range — see `pipeline/clean.py` for
> the exact bounds.
>
> **Note on the large CSV file:** the trip data file is ~650MB, which
> exceeds GitHub's 100MB per-file limit, so it is **not** included in this
> repository. Download it separately using the link in the **Dataset**
> section below and place it in `data/raw/` before running the pipeline.
> The zone lookup CSV and shapefile are small enough to ship in the repo
> directly.

---

## Video Walkthrough

> 📹 [Link to video walkthrough — insert your URL here]

---

## Project Structure

```
nyc-taxi-dashboard/
│
├── pipeline/                   # Task 1 — Data Processing & Cleaning
│   ├── data_loader.py          # Load trip CSV, zone lookup CSV, shapefile
│   ├── clean.py                # Remove nulls, duplicates, outliers
│   ├── feature_engineering.py  # 7 derived features
│   ├── integrate.py            # Join shapefile + zone lookup → GeoJSON
│   └── cleaning_log.py         # Audit trail of all exclusions
│
├── database/                   # Task 2 — Database Design & Implementation
│   ├── schema.sql              # Normalised schema (trips, zones, rate_codes)
│   ├── insert.py               # Streaming batch-insert into SQLite/PostgreSQL
│   └── queries.sql             # Full analytical query library
│
├── backend/                    # Task 3 (Backend) — Flask REST API
│   └── app.py                  # 17 JSON endpoints serving the dashboard
│
├── front/                      # Task 3 (Frontend) — Dashboard UI
│   ├── index.html              # Single-page shell — When / Where / How Much tabs
│   ├── style.css                # Full GitHub-dark-style component system
│   └── app.js                  # API calls, chart rendering, table/filter logic
│
├── data/
│   ├── raw/
│   │   ├── yellow_tripdata_2019-01.csv   # ⬇ DOWNLOAD SEPARATELY — see Dataset section
│   │   ├── taxi_zone_lookup.csv          # 265 zones — included in repo
│   │   └── taxi_zones.shp (+ .dbf/.shx/.prj/.sbn/.sbx)  # included in repo, optional
│   └── processed/              # Pipeline output (auto-generated, gitignored)
│
├── run_pipeline.py             # Task 1 entry point — runs full ETL
├── requirements.txt
├── .env.example
└── README.md
```

---

## Dataset

| File | Rows | Description | Where to get it |
|------|------|-------------|------------------|
| `yellow_tripdata_2019-01.csv` | ~7.67M | Fact table — Jan 2019 trip records (~650MB) | **[⬇ Download from NYC TLC](https://drive.google.com/file/d/1KvgSostr9SUd0DvtCkUkeVQHE1MpXG90/view?usp=drive_link)** ¹ |
| `taxi_zone_lookup.csv` | 265 | Dimension — zone names, boroughs, service zones | Already in this repo (`data/raw/`) |
| `taxi_zones.shp` (+ sidecar files) | 263 | Spatial — zone boundary polygons (optional) | Already in this repo (`data/raw/`) |

**The trip CSV is too large for GitHub (650MB vs GitHub's 100MB file limit)**,
so it's hosted externally. After downloading it, place it at:
```
data/raw/yellow_tripdata_2019-01.csv
```

> ¹ **Note on the TLC file format:** The NYC TLC now distributes 2019 data as
> `.parquet` rather than `.csv`. If you download the parquet file, convert it
> to CSV first (one-liner below), or ask your instructor if a CSV mirror link
> was provided for this assignment.
>
> **Windows (CMD) / macOS / Linux — convert parquet → CSV:**
> ```python
> # Run this once from the project root with your venv active
> import pandas as pd
> df = pd.read_parquet("data/raw/yellow_tripdata_2019-01.parquet")
> df.to_csv("data/raw/yellow_tripdata_2019-01.csv", index=False)
> print(f"Done — {len(df):,} rows written")
> ```
> Save the snippet as `convert.py` and run `python convert.py` (Windows) or
> `python3 convert.py` (macOS/Linux) from the project root. This requires
> `pyarrow` which is already in `requirements.txt`.

The `data/processed/` folder is generated automatically by `run_pipeline.py`
and is excluded from git — you don't need to (and shouldn't) commit it.

---

## Setup & Installation

> Commands are shown for **Windows (CMD)** and **macOS/Linux (bash)** side by side.
> Use whichever matches your terminal.

### 1. Open a terminal in the project folder

**Windows (CMD):**
```cmd
cd C:\path\to\nyc-taxi-dashboard
```

**macOS / Linux (bash):**
```bash
cd ~/path/to/nyc-taxi-dashboard
```

### 2. Create a Python virtual environment

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux (bash):**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your prompt once it's active.

### 3. Install dependencies

**Windows (CMD):**
```cmd
pip install -r requirements.txt
```

**macOS / Linux (bash):**
```bash
pip3 install -r requirements.txt
```

> If `geopandas` fails to install (common on Windows due to missing C++ build
> tools), skip it — it's only used for the optional shapefile/GeoJSON export.
> The rest of the pipeline runs fine without it:
> ```
> pip install pandas pyarrow numpy flask flask-cors python-dotenv
> ```

### 4. Configure environment (optional)

**Windows (CMD):**
```cmd
copy .env.example .env
```

**macOS / Linux (bash):**
```bash
cp .env.example .env
```

Edit `.env` if you want to use PostgreSQL instead of the SQLite default.

---

## Running the Project

**Important — run every command from the project root folder** (where `README.md`
lives), with your virtual environment active. All scripts use absolute internal
paths, so it doesn't matter which subfolder you were in last — just `cd` back
to the project root before each step below.

### Step 1 — Run the data pipeline (Task 1)

**Windows (CMD):**
```cmd
python run_pipeline.py
```

**macOS / Linux (bash):**
```bash
python3 run_pipeline.py
```

This will:
- Load `yellow_tripdata_2019-01.csv` (~7.67M raw rows) and `taxi_zone_lookup.csv`
- Clean the data (remove nulls, duplicates, outliers)
- Engineer 7 derived features
- Join zone names onto trips
- Output cleaned data to `data/processed/`
- Save a `cleaning_log.csv` audit trail

This step processes ~7.4 million rows and reads a ~656MB CSV, so it can take
a few minutes depending on your machine — this is expected, not a hang.

You should see it end with:
```
  PIPELINE COMPLETE
  Output folder: ...\data\processed
Next step: run  python database/insert.py
```

### Step 2 — Set up the database (Task 2)

**Windows (CMD):**
```cmd
python database\insert.py
```

**macOS / Linux (bash):**
```bash
python3 database/insert.py
```

This will:
- Create `nyc_taxi.db` (SQLite) in the project root
- Apply `schema.sql` (3 tables, 12 indexes)
- Insert all 265 zone dimension records (including TLC's "Unknown" and
  "Outside of NYC" placeholder zones, IDs 264/265)
- Stream-insert all ~7.4M cleaned trip records in batches (avoids loading
  the entire dataset into memory at once)

This step also takes a few minutes — you'll see a live progress counter
(`rows/s`) while it runs.

You should see a verification block like:
```
── Verification ──────────────────────────────────
  rate_codes               6 rows
  zones                  265 rows
  trips           7,438,614 rows
```

### Step 3 — Start the backend API (Task 3)

**Windows (CMD):**
```cmd
python backend\app.py
```

**macOS / Linux (bash):**
```bash
python3 backend/app.py
```

Leave this terminal window open — the API runs at `http://localhost:5000`
Health check: `http://localhost:5000/api/health`

### Step 4 — Open the dashboard

The dashboard is API-driven and requires the Flask backend from Step 3 to be running.

Open your browser and go to: **http://localhost:5000**

Flask serves `front/index.html`, which calls the API directly (`http://127.0.0.1:5000/api/...`)
to populate every chart, stat, and table. If the backend isn't running, the page will load
but show empty/dash placeholders — check your terminal for the Flask server and the browser
console for any failed fetch requests.

---

## Dashboard Pages

The dashboard uses a 3-tab layout (not a sidebar) — click between tabs at the top:

| Tab | Description |
|-----|-------------|
| **When** | Total trips, peak/quietest hour, avg fare by hour chart, hourly breakdown table (filterable by morning/afternoon/evening/night) |
| **Where** | Top borough, avg distance, active zones, borough trip-share bar, borough stats table, top pickup zones table (filterable by borough) |
| **How Much** | Avg fare, avg tip %, credit card %, payment type breakdown bars, fare distribution chart, payment breakdown table |

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

## Troubleshooting

**`FileNotFoundError: yellow_tripdata_2019-01.csv` (or similar)**
→ This is the large trip-data CSV (~650MB) — it's hosted externally, not
included in this repository (GitHub caps individual files at 100MB).
Download it from the link in the **Dataset** section above and place it
at `data/raw/yellow_tripdata_2019-01.csv`.

**`FileNotFoundError: zones_clean.csv not found`** or **`data/processed/ folder not found`**
→ You ran `database/insert.py` before `run_pipeline.py`. Always run the
pipeline first — it generates the files that `insert.py` needs.

**`ModuleNotFoundError: No module named 'pipeline'`**
→ You're running a script from inside a subfolder. Always `cd` back to the
project root (where `README.md` is) before running any command, and make
sure your virtual environment is active — you should see `(venv)` in your prompt.

**`ModuleNotFoundError: No module named 'pyarrow'` (or `flask_cors`, or any other dependency) — even after `pip install`**
→ This means you're running scripts with your **system Python** instead of the
**venv Python**, so packages installed into the venv aren't visible. This commonly
happens when you launch scripts with an explicit `python.exe` path rather than
the activated venv's `python`.

Fix — install all dependencies directly into the Python interpreter you're using
to run the scripts:

Windows (CMD):
```cmd
rem First make sure you're in the project root (NOT inside venv\ or any subfolder)
cd C:\path\to\nyc-taxi-dashboard

rem Install into your system Python (replace the path below with yours if different)
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r requirements.txt

rem Then run scripts with that same interpreter
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\python.exe run_pipeline.py
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\python.exe database\insert.py
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\python.exe backend\app.py
```

macOS / Linux (bash):
```bash
# Make sure you're in the project root
cd ~/path/to/nyc-taxi-dashboard

# Activate the venv, then install — this ensures pip targets the right interpreter
source venv/bin/activate
pip3 install -r requirements.txt

# Run scripts normally (venv python is used automatically when venv is active)
python3 run_pipeline.py
python3 database/insert.py
python3 backend/app.py
```

> **Root cause:** `pip install pyarrow` installs into whichever Python environment
> `pip` belongs to — which may not be the same Python that actually runs your
> scripts. Running `pip show pyarrow` showing it installed is not enough; the
> package must be in the `site-packages` of the **exact interpreter** you launch
> the script with. The safest habit is: always activate the venv first, then use
> plain `python` / `python3` (not a hardcoded path) for every command.

**`No such file or directory: run_pipeline.py` (or any project file) — even though the file exists**
→ You are running the command from inside the `venv\` subfolder (or another
subfolder). The scripts must be run from the **project root** — the folder that
contains `README.md`, `run_pipeline.py`, and `requirements.txt`.

Windows (CMD):
```cmd
rem Wrong — inside the venv subfolder
(venv) C:\...\heh\venv> python run_pipeline.py   ← ERROR

rem Correct — back in the project root
(venv) C:\...\heh\venv> cd ..
(venv) C:\...\heh> python run_pipeline.py         ← OK
```

macOS / Linux (bash):
```bash
# Wrong — inside the venv subfolder
(venv) ~/heh/venv$ python3 run_pipeline.py   # ERROR

# Correct — back in the project root
(venv) ~/heh/venv$ cd ..
(venv) ~/heh$ python3 run_pipeline.py         # OK
```

**`geopandas` fails to install on Windows**
→ Safe to skip. It's only used for optional shapefile/GeoJSON export.
```cmd
pip install pandas pyarrow numpy flask flask-cors python-dotenv
```

**`MemoryError` or the process gets killed during `run_pipeline.py` or `database/insert.py`**
→ The dataset is ~7.4M rows; on machines with limited RAM (under ~4GB free)
this can be tight. Close other applications before running, or process the
CSV in smaller date-range chunks if you need to. Most modern machines with
8GB+ RAM will run this without issue.

**Port 5000 already in use**

Windows (CMD):
```cmd
set PORT=5001
python backend\app.py
```

macOS / Linux (bash):
```bash
PORT=5001 python3 backend/app.py
```

Then visit `http://localhost:5001` instead.

**Dashboard loads but every chart/stat is blank**
→ The Flask backend (Step 3) isn't running, or the database wasn't populated.
Open the browser console (F12) and check for failed `fetch` requests to
`/api/...` — then confirm `python backend/app.py` is running in a terminal
and `nyc_taxi.db` exists in the project root.

**Some API endpoints feel slow (5-15 seconds) on first load**
→ Aggregate queries across 7.4M rows (e.g. `/api/borough-summary`,
`/api/payment-breakdown`) can take a few seconds depending on disk speed.
This is normal for SQLite on a dataset this size — it's not a hang.

---

## Key Design Decisions

### Why SQLite (default)?
Zero setup — runs immediately without a database server. The schema is fully PostgreSQL-compatible; switching is one line in `.env`.

### Why Flask?
Lightweight, beginner-friendly, and perfectly suited to a read-heavy analytics API. No ORM overhead needed since all queries are pre-written SQL.

### Why vanilla HTML/CSS/JS (no React/Vue)?
The assignment specifies HTML, CSS, and JavaScript. The dashboard uses a module pattern (`CHARTS`, `DATA`, `ALGO`, `ZONES_MODULE`) to keep code organised without a framework.

### Schema normalisation
The `zones` and `rate_codes` dimension tables avoid repeating strings across 7.4M trip rows — saving significant storage and enabling fast `JOIN`-based borough/service-zone filters.

### Custom algorithm
The max-heap in `algo.js` and `database/insert.py` uses no built-in `sort()`, `heapq`, or `Counter`. It's implemented from scratch to satisfy the algorithmic data structure requirement.

---

## Data Cleaning Summary

Verified results from an actual pipeline run against the full dataset
(7,667,792 raw rows → 7,438,614 cleaned rows, 97.0% retained):

| Step | Records removed | Reason |
|------|----------------|--------|
| Duplicates | 0 | Exact duplicate rows |
| Null critical fields | 0 | Missing datetime/location/fare |
| Out-of-range dates | 3,454 | Outside January 2019 |
| Negative duration | 6,289 | Dropoff before or equal to pickup |
| Duration outliers | 87,887 | Under 60s or over 3 hours |
| Fare outliers | 6,263 | Below $2.50 or above $500 |
| Distance outliers | 10,458 | Below 0.01mi or above 150mi |
| Passenger outliers | 114,739 | Outside 1–6 range |
| Invalid rate code | 88 | Unknown `ratecodeid` values |
| **Total excluded** | **229,178** | **3.0% of raw data** |

Full audit trail saved to `data/processed/cleaning_log.csv` after running
`run_pipeline.py`.

### Data quality note: special placeholder zones

The TLC zone lookup includes two non-geographic placeholder zones with
blank fields in the source CSV:

- **Zone 264 — "Unknown"**: blank `zone_name`/`service_zone`
- **Zone 265 — "Outside of NYC"**: blank `borough`/`service_zone`

These aren't data errors — they're valid TLC codes used when a trip's
pickup or dropoff couldn't be matched to a specific zone. **159,822 trips
(2.1% of the cleaned dataset)** reference one of these zones. Naively
dropping rows with null fields here would have silently discarded real
trips and their dependent foreign-key rows, so `pipeline/data_loader.py`
and `database/insert.py` explicitly fill these blanks (`"Unknown"` / `"N/A"`)
rather than excluding them. This is a good example of a data quality issue
worth highlighting in the technical report's "unexpected observation" section.

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
| Frontend | HTML5, CSS3, Vanilla JavaScript (API-driven, GitHub-dark styling) |
| Charts | Chart.js |
