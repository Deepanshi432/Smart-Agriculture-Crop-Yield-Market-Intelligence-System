# Smart Agriculture: Crop Yield & Market Intelligence System

Analyse weather, soil and crop data to **predict crop yield**, **recommend suitable crops** and
**explore market-price trends**.

| Module | Owner | Folder / Key Files | Status |
|---|---|---|---|
| Data analytics (cleaning, EDA, SQL, Streamlit dashboard) | Deepanshi | `data-analytics/` (`app.py`, `notebooks/`, `sql/`) | Done |
| Machine learning (yield model, crop recommender) | Lakshmi (with Deepanshi support) | `ml/`, `models/`, `data-analytics/models/` | In Progress / Baseline Ready |
| API + UI (Flask backend & Smart Agro web frontend) | Completed by Deepanshi (Philip unavailable) | `Backend/app.py`, `Frontend/index.html` | Done |

> **Note on Large Files & `.gitignore`:** GitHub enforces a **100 MB per-file size limit**. Large local artifacts such as trained model binaries (`*.pkl`), SQLite databases (`*.db`), and large processed CSV files are excluded via `.gitignore` and generated or loaded locally during development/execution.

---

## 1. What is in the project (folder structure)

```text
Smart-Agriculture-Crop-Yield-Market-Intelligence-System/
├── README.md
├── requirements.txt
├── .gitignore
├── Backend/
│   └── app.py                    # Flask API (/api/health, /api/options, /api/summary, /api/predict, /api/mandi)
├── Frontend/
│   └── index.html                # Smart Agro web UI (Yield Estimator, Top Crops, Mandi Explorer)
├── models/                       # local model artifacts (gitignored if large)
├── data-analytics/
│   ├── app.py                    # Streamlit interactive dashboard
│   ├── data/
│   │   ├── raw/                  # original files - NEVER edit by hand
│   │   │   ├── Crop_Production_Statistics.csv
│   │   │   ├── Sub_Division_IMD_2017.csv
│   │   │   ├── Crop_recommendation.csv
│   │   │   └── mandi_prices.csv
│   │   └── processed/            # created by scripts/notebooks (gitignored if large)
│   │       ├── cleaned_crop_data.csv
│   │       ├── cleaned_rainfall.csv
│   │       ├── merged_yield_data.csv      # <- input for the ML model
│   │       ├── processed_crop_data.csv
│   │       └── cleaned_mandi_prices.csv
│   ├── models/                   # analytics/model artifacts (gitignored if large)
│   ├── notebooks/                # 02_eda.ipynb, 03_sql_analysis.ipynb, eda_and_cleaning.py
│   ├── scripts/                  # pipeline scripts (if run via CLI)
│   └── sql/                      # queries.sql (+ local agriculture.db if generated)
└── ml/                           # ML module folder (if present)