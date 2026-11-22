from pathlib import Path
import sqlite3
import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data-analytics" / "data" / "processed"
DB_PATH = BASE_DIR / "data-analytics" / "sql" / "agriculture.db"

MODEL_CANDIDATES = [
    BASE_DIR / "models" / "crop_yield_model.pkl",
    BASE_DIR / "data-analytics" / "models" / "crop_yield_model.pkl",
]

DATA_CANDIDATES = [
    DATA_DIR / "merged_yield_data.csv",
    DATA_DIR / "processed_crop_data.csv",
    DATA_DIR / "cleaned_crop_data.csv",
]

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


def load_crop_df():
    for path in DATA_CANDIDATES:
        if path.exists():
            return pd.read_csv(path, low_memory=False), path.name
    return pd.DataFrame(), None


def load_model():
    for path in MODEL_CANDIDATES:
        if path.exists() and path.stat().st_size < 250 * 1024 * 1024:
            try:
                return joblib.load(path), str(path.relative_to(BASE_DIR))
            except Exception:
                pass
    return None, None


DF, DATA_SOURCE = load_crop_df()
MODEL, MODEL_SOURCE = load_model()


def get_col(df, *names):
    lower_map = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return None


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "data_loaded": not DF.empty,
        "data_source": DATA_SOURCE,
        "model_loaded": MODEL is not None,
        "model_source": MODEL_SOURCE,
        "sqlite_exists": DB_PATH.exists(),
    })


@app.route("/api/options")
def options():
    if DF.empty:
        return jsonify({"states": [], "districts": [], "crops": [], "seasons": []})

    state_col = get_col(DF, "State", "state")
    dist_col = get_col(DF, "District", "district")
    crop_col = get_col(DF, "Crop", "crop")
    season_col = get_col(DF, "Season", "season")

    selected_state = request.args.get("state")
    districts = []
    if dist_col:
        sub = DF
        if selected_state and state_col:
            sub = sub[sub[state_col].astype(str) == selected_state]
        districts = sorted(sub[dist_col].dropna().astype(str).unique().tolist())[:300]

    return jsonify({
        "states": sorted(DF[state_col].dropna().astype(str).unique().tolist()) if state_col else [],
        "districts": districts,
        "crops": sorted(DF[crop_col].dropna().astype(str).unique().tolist()) if crop_col else [],
        "seasons": sorted(DF[season_col].dropna().astype(str).unique().tolist()) if season_col else [],
    })


@app.route("/api/summary")
def summary():
    if DF.empty:
        return jsonify({
            "total_records": 0,
            "states_count": 0,
            "crops_count": 0,
            "top_crops": [],
        })

    state_col = get_col(DF, "State", "state")
    crop_col = get_col(DF, "Crop", "crop")
    prod_col = get_col(DF, "Production", "production")

    top_crops = []
    if crop_col and prod_col:
        grouped = (
            DF.groupby(crop_col, as_index=False)[prod_col]
            .sum()
            .sort_values(by=prod_col, ascending=False)
            .head(10)
        )
        top_crops = [
            {"crop": str(r[crop_col]), "production": round(float(r[prod_col]), 2)}
            for _, r in grouped.iterrows()
        ]

    return jsonify({
        "total_records": int(len(DF)),
        "states_count": int(DF[state_col].nunique()) if state_col else 0,
        "crops_count": int(DF[crop_col].nunique()) if crop_col else 0,
        "top_crops": top_crops,
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json(force=True) or {}
    state = str(payload.get("state", "")).strip()
    district = str(payload.get("district", "")).strip()
    crop = str(payload.get("crop", "")).strip()
    season = str(payload.get("season", "")).strip()
    year = int(payload.get("year", 2020))
    area = float(payload.get("area", 100.0))

    yield_col = get_col(DF, "Yield", "yield") if not DF.empty else None
    crop_col = get_col(DF, "Crop", "crop") if not DF.empty else None
    state_col = get_col(DF, "State", "state") if not DF.empty else None

    estimated_yield = None
    method = "dataset_average_fallback"

    if not DF.empty and yield_col and crop_col:
        sub = DF[DF[crop_col].astype(str).str.lower() == crop.lower()]
        if state and state_col:
            sub_state = sub[sub[state_col].astype(str).str.lower() == state.lower()]
            if not sub_state.empty:
                sub = sub_state
        if not sub.empty:
            estimated_yield = float(sub[yield_col].dropna().median())

    if estimated_yield is None:
        estimated_yield = 2.5

    estimated_production = round(estimated_yield * max(area, 0.0), 2)

    return jsonify({
        "state": state,
        "district": district,
        "crop": crop,
        "season": season,
        "year": year,
        "area": area,
        "predicted_yield": round(estimated_yield, 2),
        "estimated_production": estimated_production,
        "method": method,
    })


@app.route("/api/mandi")
def mandi():
    commodity = request.args.get("commodity", "").strip().lower()
    mandi_csv = DATA_DIR / "cleaned_mandi_prices.csv"

    if mandi_csv.exists():
        mdf = pd.read_csv(mandi_csv, low_memory=False)
        comm_col = get_col(mdf, "Commodity", "commodity")
        if commodity and comm_col:
            mdf = mdf[mdf[comm_col].astype(str).str.lower().str.contains(commodity, na=False)]
        return jsonify({
            "source": "cleaned_mandi_prices.csv",
            "rows": mdf.head(20).fillna("").to_dict(orient="records"),
        })

    if DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH) as conn:
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                mandi_table = next((t for t in tables if "mandi" in t.lower()), None)
                if mandi_table:
                    query = f"SELECT * FROM {mandi_table} LIMIT 20"
                    rows = pd.read_sql_query(query, conn).fillna("").to_dict(orient="records")
                    return jsonify({"source": f"sqlite:{mandi_table}", "rows": rows})
        except Exception as e:
            return jsonify({"source": "sqlite_error", "error": str(e), "rows": []})

    return jsonify({"source": "none", "rows": []})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)