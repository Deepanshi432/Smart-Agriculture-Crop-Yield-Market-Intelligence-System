"""Shared paths and helpers. Every script imports this, so you can run them from any folder."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]      # .../data-analytics
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
SQL_DIR = BASE / "sql"
CHARTS = BASE / "dashboard" / "charts"
DB_PATH = SQL_DIR / "agriculture.db"

for p in (PROCESSED, SQL_DIR, CHARTS):
    p.mkdir(parents=True, exist_ok=True)


def find_raw(pattern: str) -> Path:
    """Find a raw file by pattern (so 'Crop_recommendation_1.csv' style names also work)."""
    files = sorted(RAW.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matching '{pattern}' in {RAW}")
    return files[0]


def clean_text(s):
    """Strip edges and collapse repeated inner spaces."""
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
