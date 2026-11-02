# Chandigarh Road Safety Intelligence System

A self-contained, single-origin web application and descriptive analytics platform for urban road safety exploration in Chandigarh. The system evaluates spatial crash patterns across fixed metric grid cells, tracks emerging incident clusters, and models counterfactual intervention policies.

> [!IMPORTANT]
> **SYNTHETIC DEMONSTRATION DATA — NOT VERIFIED REAL-WORLD CRASH RECORDS**  
> All 10,000 incident records, casualty figures, and analytical outcomes in this project are synthetically generated for academic demonstration and software evaluation. Corridor geometries are derived from OpenStreetMap; incident coordinates and attributes are simulated. This project is not an official traffic authority tool or a validated predictive safety model.

---

## 1. What the Project Does & Problem Solved

Traditional traffic accident reporting often relies on administrative boundaries (e.g., police station jurisdictions or sectors) that mask local collision clusters and fail to capture corridor-level danger zones.

This project addresses this by providing:
- **Spatial Grid Hotspotting**: Bins incidents into uniform 500m × 500m UTM grid cells (EPSG:32643) with frozen baseline percentiles (75th and 90th percentile burden) to identify high-density crash clusters independent of administrative boundaries.
- **Severity Burden Indexing**: Separates raw incident counts from weighted societal impact using an illustrative burden metric ($3 \times \text{Fatal} + 2 \times \text{Serious} + 1 \times \text{Minor}$).
- **Emerging Hotspot Tracking**: Evaluates two equal 90-day observation windows with guardrails ($\ge 5$ baseline, $\ge 10$ recent, $\ge 5$ increase, $\ge 1.5\times$ ratio) to flag rapidly escalating incident areas.
- **Counterfactual Intervention Lab**: Models what-if scenarios (speed management, junction redesign, lighting, pedestrian facilities) with transparent scaling and user-adjustable intensity and effectiveness.
- **Zero-Dependency Deployment**: Functions entirely offline without external databases, paid map API keys, or cloud services.

---

## 2. How the Application Works

### System Architecture & Data Flow

```
+-------------------------------------------------------------------------+
|                              DATA PIPELINE                              |
|  data/raw/osm-road-source.json  -->  scripts/prepare_geography.py       |
|                                        |--> data/processed/anchors.json |
|                                        +--> static/roads.geojson        |
|                                                                         |
|  scripts/generate_data.py (Seed 20261022)                               |
|       +--> data/synthetic/incidents.csv (10,000 records)                |
|       +--> data/synthetic/manifest.json (SHA-256 Checksum)              |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                             FASTAPI BACKEND                             |
|  backend/domain.py      -> Paths, taxonomies, severity weights, models  |
|  backend/validation.py  -> Schema auditing, bounds check, derived features|
|  backend/analytics.py   -> UTM 43N projection, 500m grid, aggregations  |
|  backend/reports.py     -> Server-side PDF generation with ReportLab    |
|  backend/main.py        -> REST API endpoints, GZip, security headers   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           FRONTEND DASHBOARD                            |
|  static/index.html      -> Semantic single-page application shell       |
|  static/app.js          -> Client router (8 views), state, URL filters  |
|  static/style.css       -> Accessible, responsive design system         |
|  static/vendor/         -> Local Leaflet.js, Chart.js, bundled fonts    |
+-------------------------------------------------------------------------+
```

1. **Data Ingestion & Validation**: On startup, `backend/analytics.py` loads `data/synthetic/incidents.csv` and `data/processed/anchors.json`. `backend/validation.py` audits required fields, date formats, coordinate bounds ($30.69^\circ\text{–}30.77^\circ\text{ N}, 76.73^\circ\text{–}76.83^\circ\text{ E}$), and casualty consistency.
2. **Spatial Indexing**: Coordinates are projected to UTM Zone 43N (`EPSG:32643`). Incidents are binned into fixed metric cells:
   $$\text{gx} = \lfloor\text{easting} / 500\rfloor, \quad \text{gy} = \lfloor\text{northing} / 500\rfloor, \quad \text{cell\_id} = \text{gx\_gy}$$
3. **API Delivery**: FastAPI delivers filtered metrics, paginated incident logs, area dossiers, scenario simulations, and state-sensitive CSV/PDF exports.
4. **Client-Side Rendering**: Vanilla JavaScript manages hash-based routing (`#overview`, `#explorer`, `#analytics`, etc.), renders maps with Leaflet, and visualizes distributions with Chart.js.

---

## 3. Technologies Used

- **Backend**: Python 3.13+, FastAPI, Uvicorn, Pandas, NumPy, PyProj, ReportLab, Pydantic.
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3, Leaflet.js (bundled offline), Chart.js (bundled offline), OpenStreetMap GeoJSON.
- **Testing & Quality Assurance**: Pytest, HTTPX, Playwright (Chromium E2E testing).
- **Packaging & Environment**: Standard `venv` / `pip` or `uv`.

---

## 4. Folder Structure

```
chdroadintelligence/
├── backend/                  # Server-side application and analytics engine
│   ├── __init__.py           # Package indicator
│   ├── analytics.py          # Spatial binning, filtering, metrics, and simulations
│   ├── domain.py             # Paths, domain constants, taxonomies, and interventions
│   ├── main.py               # FastAPI entry point, endpoints, and middleware
│   ├── reports.py            # ReportLab PDF report generation
│   └── validation.py         # Input schema validation and feature derivation
├── data/                     # Data assets (cleanly separated by provenance)
│   ├── raw/                  # Raw external data (OSM API JSON extract)
│   │   └── osm-road-source.json
│   ├── processed/            # Derived corridor anchors and provenance metadata
│   │   ├── anchors.json
│   │   └── geography-provenance.json
│   └── synthetic/            # Synthetic demonstration records and manifest
│       ├── incidents.csv     # 10,000 synthetic incident records
│       └── manifest.json     # Checksum and generation parameters
├── docs/                     # Technical documentation and test outputs
│   ├── browser-results.json  # Playwright functional flow verification log
│   ├── design-review.md      # UI/UX design review and audit notes
│   ├── REFERENCE_REVIEW.md   # Architectural comparison notes
│   ├── resilience-results.json # Browser resilience and accessibility test log
│   └── VERIFICATION.md       # Comprehensive verification records
├── outputs/                  # Export artifacts and generated reports
├── scripts/                  # Data engineering and regeneration scripts
│   ├── fetch_geography.py    # Optional live OSM API tile downloader
│   ├── generate_data.py      # Deterministic 10,000-row synthetic crash generator
│   └── prepare_geography.py  # Builds anchors, GeoJSON roads, and provenance
├── static/                   # Static frontend assets (served by FastAPI)
│   ├── fonts/                # Local offline fonts (Barlow, DM Sans)
│   ├── licenses/             # Open-source third-party licenses
│   ├── vendor/               # Offline Leaflet and Chart.js libraries
│   ├── app.js                # Core frontend SPA application (8 views)
│   ├── favicon.svg           # Brand vector icon
│   ├── index.html            # Main dashboard HTML shell
│   ├── roads.geojson         # Extracted road network geometry
│   └── style.css             # Application stylesheet
├── tests/                    # Automated testing suite
│   ├── browser_flows.py      # Playwright E2E browser tests across all 8 views
│   ├── browser_resilience.py # Fault-injection, rapid-nav, and a11y tests
│   └── test_system.py        # 29 backend unit and integration tests
├── .gitignore                # Git exclusion rules
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Production runtime dependencies
├── requirements-dev.txt      # Development and testing dependencies
└── README.md                 # Project documentation
```

---

## 5. Important Files & What Each One Does

| File | Component | Purpose |
|---|---|---|
| `backend/main.py` | Backend API | Main application entry point; defines REST routes, security headers, GZip, and static asset serving. |
| `backend/analytics.py` | Analytics Engine | Transforms coordinates to UTM 43N, computes 500m cells, aggregates metrics, and runs counterfactual scenarios. |
| `backend/domain.py` | Domain Config | Central repository of file paths, severity weights, categorical lists, and intervention definitions. |
| `backend/validation.py` | Validation | Validates dataset rows against schema constraints, captures errors in an auditable log, and derives temporal features. |
| `backend/reports.py` | Reporting | Generates multi-page, publication-quality PDF reports with embedded charts and vector schematics. |
| `static/app.js` | Frontend Router | Single-page application logic managing 8 views, URL state synchronization, Leaflet maps, and Chart.js charts. |
| `static/index.html` | Frontend UI | Semantic HTML dashboard container with sidebar navigation, filter controls, and alert regions. |
| `data/synthetic/incidents.csv` | Dataset | 10,000 reproducible synthetic incident records spanning July 2024 to June 2026. |
| `data/processed/anchors.json` | Geospatial | 18 well-spaced corridor anchor segments extracted from OpenStreetMap. |
| `scripts/generate_data.py` | Generator | Deterministic data generator producing byte-for-byte identical synthetic incident records using seed 20261022. |
| `scripts/prepare_geography.py` | GIS Pipeline | Filters OSM ways, calculates anchor centroids, and generates `static/roads.geojson`. |
| `tests/test_system.py` | Test Suite | 29 automated tests verifying dataset reproducibility, grid invariance, security, and analytical calculations. |

---

## 6. Installation & Setup

### Prerequisites
- **Python**: Version 3.13 or 3.14 (Python 3.13 recommended).
- **OS**: Windows 10/11 (fully supported; also works on macOS and Linux).
- **Git** (optional).

### Step-by-Step Installation (Windows PowerShell)

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd C:\path\to\chdroadintelligence-main
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

4. Install dependencies:
   ```powershell
   pip install -r requirements-dev.txt
   ```
   *(Or install runtime only via `pip install -r requirements.txt`).*

---

## 7. Exact Commands to Run the Project on Windows

With your virtual environment activated:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

You will see:
```
INFO:     Started server process [pid]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

To run on default port 8000 instead, change `--port 8000`.

---

## 8. How to Access and Use the Dashboard

1. Open your web browser (Chrome, Edge, Firefox, or Brave) and navigate to:
   ```
   http://127.0.0.1:8765
   ```
2. Explore the eight dedicated views via the left sidebar:
   - **Overview (`#overview`)**: Executive summary cards, severity ledger, monthly/hourly crash trends, and top corridor rankings.
   - **Hotspot Explorer (`#explorer`)**: Interactive Leaflet map with toggleable layers (Incident markers, 500m Metric Grid, Density circles, Emerging clusters), cell selection inspector, and paginated incident table.
   - **Analytics Studio (`#analytics`)**: Multi-dimensional breakdowns (factors, vehicle types, road user types, weather conditions, hour-of-day vs severity matrix) with Pareto cumulative share tables.
   - **Area Dossiers (`#dossiers`)**: Deep-dive profile for any selected corridor anchor or grid cell, comparing local metrics against citywide baselines and recommending candidate interventions.
   - **Comparison Lab (`#comparison`)**: Side-by-side comparison of two road corridors across severity, vehicle mix, and hourly distributions.
   - **Intervention Lab (`#intervention`)**: Interactive policy simulator. Adjust intervention type, implementation intensity ($0\%\text{–}100\%$), duration ($1\text{–}36$ months), and assumed effectiveness to project expected casualty reductions and hypothetical costs.
   - **Reports & Export (`#exports`)**: Filter-sensitive downloads for CSV (incidents, areas, hotspots) and publication-ready multi-page PDF reports.
   - **Data & Methodology (`#methodology`)**: Complete documentation of simulation assumptions, dataset schema, OSM geography provenance, and live data preview.
3. **Filtering**: Use the top filter bar to filter by date range, corridor area, severity, vehicle, factor, and time of day (Day/Night). Click **Apply** to update all views simultaneously.

---

## 9. How to Run Tests and Regenerate Data

### Run Automated Backend Tests
Ensure the virtual environment is active and run pytest:
```powershell
pytest -q
```
All 29 tests should pass in under 10 seconds.

### Run End-to-End Browser Tests (Optional)
Start the server in one terminal:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```
In a second terminal, execute the browser verification scripts:
```powershell
python tests/browser_flows.py
python tests/browser_resilience.py
```

### Regenerate Data
To regenerate the exact 10,000 synthetic incident records and verify checksums:
```powershell
python scripts/generate_data.py
```
To re-extract road anchors from the raw OSM snapshot:
```powershell
python scripts/prepare_geography.py
```

---

## 10. Important Limitations

1. **Synthetic Nature**: The dataset is entirely generated using statistical distributions and pseudorandom sampling. It must **never** be cited as real crash statistics or used for real-world traffic enforcement decisions.
2. **Geographical Scope**: Geography reflects a curated extract of 18 major Chandigarh road corridors and does not cover the complete road network or minor residential streets.
3. **Simplified Spatial Buffering**: Incident locations are interpolated along OSM corridor segments with $\pm 8\text{m}$ metric offsets; they are not dynamically snapped to road network graphs.
4. **Descriptive, Not Causal**: Scenario simulations apply deterministic percentage reductions to eligible records. They do not simulate behavioral adaptation, route diversion, or induced demand.
5. **In-Memory Architecture**: Designed for local academic evaluation. Data is loaded into memory on server startup; there is no persistent write-back database.
