# Smart Agriculture: Crop Yield & Market Intelligence System

Analyse weather, soil and crop data to **predict crop yield**, **recommend suitable crops** and
**explore market-price trends**.

| Module | Owner | Folder | Status |
|---|---|---|---|
| Data analytics (cleaning, EDA, SQL, dashboard) | Member 1 (Deepanshi) | `data-analytics/` | Done (this README) |
| Machine learning (yield model, crop recommender) | Member 2 (Lakshmi) | `ml/` | Next |
| API + UI | TBD | `backend/`, `frontend/` | Later |

---

## 1. What is in the project (folder structure)

```
Smart-Agriculture/
├── README.md
├── requirements.txt
├── data-analytics/
│   ├── data/
│   │   ├── raw/                  # original files - NEVER edit by hand
│   │   │   ├── Crop_Production_Statistics.csv
│   │   │   ├── Sub_Division_IMD_2017.csv
│   │   │   ├── Crop_recommendation.csv
│   │   │   └── mandi_prices.csv
│   │   └── processed/            # created by the scripts
│   │       ├── cleaned_crop_data.csv
│   │       ├── cleaned_rainfall.csv
│   │       ├── merged_yield_data.csv      # <- input for the ML model
│   │       └── cleaned_mandi_prices.csv
│   ├── scripts/                  # the pipeline (run in order 01 -> 06)
│   ├── sql/                      # agriculture.db + queries.sql
│   ├── dashboard/                # app.py (Plotly Dash) + charts/*.html
│   └── notebooks/                # exploration notebooks (optional)
└── ml/                           # Member 2 (not built yet)
```

## 2. The datasets: what, why, where from

| Dataset | Key columns | Why we need it | Where from |
|---|---|---|---|
| **Crop production** (district-wise, 1997-2020, 345k rows) | `State, District, Crop, Crop_Year, Season, Area, Production, Yield` | Core data: yield per crop, district, season, year | Kaggle "Crop Production Statistics" / data.gov.in / DES Agriculture |
| **Rainfall** (IMD sub-divisions, 1901-2017) | `SUBDIVISION, YEAR, JAN..DEC, ANNUAL, JF, MAM, JJAS, OND` | Weather feature for the yield model | IMD, data.gov.in "Sub-divisional monthly rainfall" |
| **Crop recommendation** (2,200 rows, 22 crops) | `N, P, K, temperature, humidity, ph, rainfall, label` | Soil + weather -> suitable crop (classification) | Kaggle `atharvaingle/crop-recommendation-dataset` |
| **Mandi prices** (7,692 rows, 146 commodities, **one day**) | `State, District, Market, Commodity, Variety, Min/Max/Modal price, date` | Market-price comparison | data.gov.in "Current Daily Price of Various Commodities (Mandi)" |

Put these four files in `data-analytics/data/raw/`.

## 3. How to run

```bash
pip install -r requirements.txt
cd Smart-Agriculture
python data-analytics/scripts/run_all.py        # runs steps 01-06
python data-analytics/dashboard/app.py          # open http://127.0.0.1:8050
```

Each script can also be run alone. They use paths relative to the project, so they work from any folder.

## 4. The pipeline step by step (what, why, how)

### Step 1 - `01_clean_crop_production.py`
**What:** cleans the raw crop table -> `processed/cleaned_crop_data.csv`.
**Why / how:**

| Problem found in raw data | Fix | Reason |
|---|---|---|
| Spaces in column names and values (`"District "`, `"Kharif     "`), double spaces in crop names | strip + collapse spaces | otherwise the same value looks like two different values |
| State spelled differently (`THE DADRA AND NAGAR HAVELI`, `Laddak`, `CHANDIGARH`) | title case + mapping | one name per state, needed for joins |
| 4,948 rows with missing Production, 9 with missing Crop | dropped | cannot analyse them |
| 1,466 rows with zero Production | dropped | in this dataset zero mostly means "not reported", not a real failure |
| 584 duplicate records (same state, district, crop, year, season) | dropped | avoids double counting |
| Extreme yields (e.g. 43,958) | per-crop IQR rule (Q3 + 3xIQR) | each crop has its own scale, so one global limit would be wrong |
| Yield column | recomputed as `Production / Area` | consistent and correct |

Result: 345,336 -> **334,630 rows** (96.9% kept).

> **Do not fill missing Production with `Area x Yield`.** On exactly those rows Yield is already 0,
> so this turns missing data into fake "zero production / crop failure" rows.

### Step 2 - `02_clean_rainfall.py`
**What:** cleans IMD rainfall and converts it from **sub-division** to **state** level -> `cleaned_rainfall.csv`.
**How:** missing months are filled with that sub-division's median for the same month; totals are rebuilt from months;
each state is mapped to its IMD sub-division(s) (average if several, e.g. Maharashtra = 4 sub-divisions).
Seasonal columns: `jjas` (Jun-Sep monsoon = Kharif), `ond` + `jf` (Rabi), `mam` (Summer), `annual`.
**Why:** crop data is by state/district, rainfall by sub-division, so they cannot be joined directly.

### Step 3 - `03_merge_yield_rainfall.py`
**What:** joins crop and rainfall on `state + year` -> `merged_yield_data.csv` (**298,118 rows, 1997-2017**).
Adds `season_rainfall` = the rainfall that matters for that row's season (Kharif -> JJAS, Rabi -> OND+JF, Summer -> MAM, others -> annual).
**Why:** this is the table the yield model learns from.
Crop rows for 2018-2020 (36,512) are dropped because IMD rainfall ends in 2017.

### Step 4 - `04_clean_mandi.py`
**What:** renames `Min_x0020_Price` -> `min_price` etc., parses dates, removes invalid prices -> `cleaned_mandi_prices.csv`.
**Limit:** the file is a **single day (01/11/2026)**, so it supports price *comparison* (state/commodity), **not price trends**.
For trends, download history (e.g. CEDA Ashoka Agmarknet portal) and re-run this script.

### Step 5 - `05_eda.py`
Saves interactive charts to `dashboard/charts/`: top rice states, yield trends of major crops, season-wise area,
wheat yield heatmap (state x year), rainfall vs yield, top rice districts.

### Step 6 - `06_load_sql.py` + `sql/queries.sql`
Loads all processed tables into `sql/agriculture.db` (SQLite) and runs six business queries:
top 5 crops per state (window function), year-over-year rice growth (`LAG`), season-wise performance,
top wheat districts, rainfall bands vs yield, most expensive commodities.

### Step 7 - `dashboard/app.py`
Plotly Dash app with filters (crop, state, season, year range), KPIs, yield trend, top districts,
rainfall vs yield and today's mandi price for the selected crop.

## 5. Findings from the EDA (use these in the report)

- Top Wheat districts are all in **Punjab** (Sangrur, Barnala, Bathinda: ~5.4-5.7 t/ha).
- Kharif rice yield is **higher in the driest band (<500 mm: 2.75 t/ha)** than in wet bands (1.65-1.93).
  The correlation between rainfall and yield is **negative** (Rice -0.29, Wheat -0.34).
  This is **not** "rain hurts crops": low-rain states (Punjab, Haryana) are heavily irrigated and have the best yields
  (a confounding effect). The model therefore **must** include `state`/`district` and `crop`; rainfall alone is misleading.
- Rice production swings year to year (e.g. -20.6% in 2002, a drought year).

## 6. Hand-off to the ML module (Member 2)

- **Yield model input:** `data/processed/merged_yield_data.csv`
  - Target: `yield` (or `log1p(yield)`). **Never use `production` as a feature** (yield = production / area, data leakage).
  - Features: `state, district, crop, season, year, area, season_rainfall, annual, jjas, ond, jf, mam`.
  - Yields of different crops are on different scales (Coconut is in nuts/ha, Sugarcane ~55 t/ha). Keep `crop` as a feature,
    or train separate models / exclude Coconut.
  - Validate with a **time split** (train up to ~2013, test 2014-2017), not only a random 80/20 split.
  - Put scaling inside a `Pipeline` (only needed for Linear Regression); export the whole pipeline with `joblib`.
- **Crop recommender input:** `data/raw/Crop_recommendation.csv`. Features `N,P,K,temperature,humidity,ph,rainfall`, target `label`.
  The data is augmented/synthetic, so very high accuracy will not mean real-world accuracy.
- Planned outputs: `ml/models/crop_yield_model.pkl`, `ml/models/crop_recommender.pkl`, `ml/predict.py` (JSON in, prediction out).

## 7. Known limitations

1. Crop data runs to 2020 but rainfall to 2017, so modelling uses 1997-2017.
2. Rainfall is state-average (not district), so it is a rough weather signal.
3. Mandi data is one day: no price trends yet.
4. Soil data (NPK, pH) is not linked to the yield data (no common key), so it only powers the crop recommender.
5. Zero/missing production rows were dropped, so real crop failures are not represented.

## 8. Troubleshooting

| Error | Fix |
|---|---|
| `No file matching ... in data/raw` | put the four raw CSVs in `data-analytics/data/raw/` |
| `ModuleNotFoundError: config` | run scripts from `data-analytics/scripts/` or use `run_all.py` |
| `FileNotFoundError ... merged_yield_data.csv` when starting the dashboard | run `run_all.py` first |
| Notebook cannot find the CSV | in `notebooks/` use `../data/raw/...`; or use `from pathlib import Path` like `scripts/config.py` |

## 9. About the existing notebook `01_data_cleaning.ipynb`

Keep it for explanation, but do not save its output as the final data:
remove the `Area x Yield` imputation and the `Crop_Failure` flag (they turn missing data into fake failures),
add duplicate removal, per-crop outlier handling and `to_csv`. The scripts in `scripts/` are the single source of truth.
