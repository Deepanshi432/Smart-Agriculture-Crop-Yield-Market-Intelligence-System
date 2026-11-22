import sqlite3
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Smart Agriculture Crop Yield & Market Intelligence",
    layout="wide",
)

st.title("🌾 Smart Agriculture Crop Yield & Market Intelligence System")
st.caption("Crop Yield Insights, Prediction & Mandi Market Analytics")

# Resolve paths relative to data-analytics/app.py
APP_DIR = Path(__file__).resolve().parent  # .../data-analytics
PROJECT_ROOT = APP_DIR.parent


def resolve_first_existing(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


PROCESSED_CSV = resolve_first_existing([
    APP_DIR / "data" / "processed" / "processed_crop_data.csv",
    PROJECT_ROOT / "data" / "processed" / "processed_crop_data.csv",
])

MODEL_PATH = resolve_first_existing([
    APP_DIR / "models" / "crop_yield_model.pkl",
    PROJECT_ROOT / "models" / "crop_yield_model.pkl",
])

DB_PATH = resolve_first_existing([
    APP_DIR / "sql" / "agriculture.db",
    PROJECT_ROOT / "sql" / "agriculture.db",
])


@st.cache_data
def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    return df


@st.cache_resource
def load_model(model_path: Path):
    return joblib.load(model_path)


if PROCESSED_CSV is None:
    expected_csv = APP_DIR / "data" / "processed" / "processed_crop_data.csv"
    st.error(f"Processed CSV not found at: {expected_csv}")
    st.stop()

df = load_data(PROCESSED_CSV)
model = load_model(MODEL_PATH) if MODEL_PATH is not None else None

# --- Helper to match case-insensitive column names ---
col_lookup = {c.lower(): c for c in df.columns}


def col(name: str) -> str | None:
    return col_lookup.get(name.lower())


state_col = col("state")
district_col = col("district")
crop_col = col("crop")
season_col = col("season")
year_col = col("year") or col("crop_year")
area_col = col("area")
prod_col = col("production")
yield_col = col("yield")

# --- Top KPIs ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Records", f"{len(df):,}")
k2.metric("States Covered", f"{df[state_col].nunique()}" if state_col else "N/A")
k3.metric("Crops Covered", f"{df[crop_col].nunique()}" if crop_col else "N/A")
k4.metric(
    "Average Yield",
    f"{df[yield_col].mean():.2f}" if yield_col else "N/A",
)

st.divider()

# --- Sidebar: Yield Prediction ---
st.sidebar.header("🌱 Crop Yield Predictor")

if model is None:
    st.sidebar.warning("Trained model (`crop_yield_model.pkl`) not found locally.")
else:
    encoded_map = {
        "state_encoded": state_col,
        "district_encoded": district_col,
        "crop_encoded": crop_col,
        "season_encoded": season_col,
    }
    model_features = list(
        getattr(
            model,
            "feature_names_in_",
            [
                c
                for c in [
                    "state_encoded",
                    "district_encoded",
                    "crop_encoded",
                    "season_encoded",
                    "year",
                    "area",
                ]
                if col(c) is not None
            ],
        )
    )

    input_values: dict[str, float | int] = {}
    selected_state_val = None

    for feat in model_features:
        feat_lower = feat.lower()
        enc_target = col(feat)

        if feat_lower == "state_encoded" and state_col and enc_target:
            states = sorted(df[state_col].dropna().astype(str).unique())
            sel_s = st.sidebar.selectbox("State", states)
            selected_state_val = sel_s
            input_values[feat] = int(
                df.loc[df[state_col].astype(str) == sel_s, enc_target].iloc[0]
            )

        elif feat_lower == "district_encoded" and district_col and enc_target:
            if state_col and selected_state_val is not None:
                dist_series = df.loc[
                    df[state_col].astype(str) == selected_state_val, district_col
                ]
            else:
                dist_series = df[district_col]
            districts = sorted(dist_series.dropna().astype(str).unique())
            sel_d = st.sidebar.selectbox("District", districts)
            input_values[feat] = int(
                df.loc[df[district_col].astype(str) == sel_d, enc_target].iloc[0]
            )

        elif feat_lower == "crop_encoded" and crop_col and enc_target:
            crops = sorted(df[crop_col].dropna().astype(str).unique())
            sel_c = st.sidebar.selectbox("Crop", crops)
            input_values[feat] = int(
                df.loc[df[crop_col].astype(str) == sel_c, enc_target].iloc[0]
            )

        elif feat_lower == "season_encoded" and season_col and enc_target:
            seasons = sorted(df[season_col].dropna().astype(str).unique())
            sel_sn = st.sidebar.selectbox("Season", seasons)
            input_values[feat] = int(
                df.loc[df[season_col].astype(str) == sel_sn, enc_target].iloc[0]
            )

        elif feat_lower in ("year", "crop_year") and year_col:
            min_y = int(df[year_col].min())
            max_y = int(max(df[year_col].max(), 2026))
            default_y = min(max_y, 2020)
            input_values[feat] = st.sidebar.number_input(
                "Crop Year", min_value=min_y, max_value=max_y, value=default_y
            )

        elif feat_lower == "area" and area_col:
            input_values[feat] = st.sidebar.number_input(
                "Area (Hectares)", min_value=0.1, value=100.0
            )

        elif enc_target is not None and pd.api.types.is_numeric_dtype(df[enc_target]):
            input_values[feat] = float(df[enc_target].median())

    if st.sidebar.button("Predict Yield"):
        missing_feats = [f for f in model_features if f not in input_values]
        if missing_feats:
            st.sidebar.error(f"Missing model features in dataset: {missing_feats}")
        else:
            X_input = pd.DataFrame([input_values])[model_features]
            pred_yield = float(model.predict(X_input)[0])
            st.sidebar.success(f"Predicted Yield: **{pred_yield:.2f}**")

# --- Dashboard Tabs ---
tab1, tab2 = st.tabs(["📊 Production & Yield Insights", "🏪 Mandi Prices (SQL)"])

with tab1:
    left, right = st.columns(2)

    if crop_col and prod_col:
        with left:
            st.subheader("Top 10 Crops by Total Production")
            top_crops = (
                df.groupby(crop_col, as_index=False)[prod_col]
                .sum()
                .sort_values(prod_col, ascending=False)
                .head(10)
            )
            st.bar_chart(top_crops.set_index(crop_col)[prod_col])
    else:
        with left:
            st.info("Crop or Production column not found in dataset.")

    if state_col and prod_col:
        with right:
            st.subheader("Top 10 States by Total Production")
            top_states = (
                df.groupby(state_col, as_index=False)[prod_col]
                .sum()
                .sort_values(prod_col, ascending=False)
                .head(10)
            )
            st.bar_chart(top_states.set_index(state_col)[prod_col])
    else:
        with right:
            st.info("State or Production column not found in dataset.")

with tab2:
    if DB_PATH is None:
        st.info("SQLite database (`agriculture.db`) not found locally.")
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table'", conn
            )["name"].tolist()
            if "mandi_prices" in tables:
                mandi_df = pd.read_sql(
                    """
                    SELECT commodity, ROUND(AVG(modal_price)) AS avg_modal_price, COUNT(*) AS markets
                    FROM mandi_prices
                    GROUP BY commodity
                    HAVING markets >= 20
                    ORDER BY avg_modal_price DESC
                    LIMIT 10
                    """,
                    conn,
                )
                st.subheader("Top 10 Commodities by Average Modal Price")
                st.dataframe(mandi_df, use_container_width=True)
            else:
                st.info("`mandi_prices` table not found in `agriculture.db`.")
            conn.close()
        except Exception as exc:
            st.warning(f"Could not query `agriculture.db`: {exc}")