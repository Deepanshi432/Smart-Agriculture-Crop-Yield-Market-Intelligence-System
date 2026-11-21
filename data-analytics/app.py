from pathlib import Path
import sqlite3
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Smart Agriculture: Crop Yield & Market Intelligence",
    layout="wide"
)

st.title("Smart Agriculture: Crop Yield & Market Intelligence")

current_file = Path(__file__).resolve()
DATA_ANALYTICS_DIR = current_file.parents[1]
PROCESSED_CSV = DATA_ANALYTICS_DIR / "data" / "processed" / "processed_crop_data.csv"
MODEL_PATH = DATA_ANALYTICS_DIR / "models" / "crop_yield_model.pkl"
DB_PATH = DATA_ANALYTICS_DIR / "sql" / "agriculture.db"

NEEDED_COLS = [
    "state", "district", "crop", "season", "year", "area", "production", "yield",
    "state_encoded", "district_encoded", "crop_encoded", "season_encoded"
]


@st.cache_data(show_spinner=False)
def load_fast_data(csv_path: Path) -> pd.DataFrame:
    header = pd.read_csv(csv_path, nrows=0).columns.str.strip().tolist()
    cols = [c for c in NEEDED_COLS if c in header]
    df = pd.read_csv(csv_path, usecols=cols, low_memory=False)
    df.columns = df.columns.str.strip()

    for col in ["state", "district", "crop", "season"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().astype("category")

    for col in ["year", "area", "production", "yield"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_resource(show_spinner=False)
def load_model(model_path: Path):
    return joblib.load(model_path)


@st.cache_data(show_spinner=False)
def load_mandi_top(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    try:
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
        if "mandi_prices" not in tables:
            return pd.DataFrame()
        return pd.read_sql(
            """
            SELECT commodity, ROUND(AVG(modal_price)) AS avg_modal_price, COUNT(*) AS markets
            FROM mandi_prices
            GROUP BY commodity
            HAVING markets >= 20
            ORDER BY avg_modal_price DESC
            LIMIT 10
            """,
            conn
        )
    finally:
        conn.close()


if not PROCESSED_CSV.exists():
    st.error(f"Processed CSV not found at: {PROCESSED_CSV}")
    st.stop()

with st.spinner("Loading dataset..."):
    df = load_fast_data(PROCESSED_CSV)

# --- Top Filter Row ---
f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 2.0])

crops = ["All"] + sorted(df["crop"].dropna().unique().tolist()) if "crop" in df.columns else ["All"]
default_crop_idx = crops.index("Rice") if "Rice" in crops else 0
sel_crop = f1.selectbox("Crop", crops, index=default_crop_idx)

states = ["All"] + sorted(df["state"].dropna().unique().tolist()) if "state" in df.columns else ["All"]
sel_state = f2.selectbox("State", states, index=0)

seasons = ["All"] + sorted(df["season"].dropna().unique().tolist()) if "season" in df.columns else ["All"]
sel_season = f3.selectbox("Season", seasons, index=0)

if "year" in df.columns and df["year"].notna().any():
    min_yr = int(df["year"].min())
    max_yr = int(df["year"].max())
    default_end = min(max_yr, 2017) if max_yr >= min_yr else max_yr
    yr_range = f4.slider("Years", min_value=min_yr, max_value=max_yr, value=(min_yr, default_end))
    yr_min, yr_max = int(yr_range[0]), int(yr_range[1])
else:
    yr_min, yr_max = None, None

# Filter directly in-memory (no large dataframe caching overhead per click)
sub = df
if sel_crop != "All" and "crop" in sub.columns:
    sub = sub[sub["crop"] == sel_crop]
if sel_state != "All" and "state" in sub.columns:
    sub = sub[sub["state"] == sel_state]
if sel_season != "All" and "season" in sub.columns:
    sub = sub[sub["season"] == sel_season]
if yr_min is not None and yr_max is not None and "year" in sub.columns:
    sub = sub[(sub["year"] >= yr_min) & (sub["year"] <= yr_max)]

records = len(sub)
avg_yield_val = float(sub["yield"].mean()) if ("yield" in sub.columns and records > 0) else 0.0
tot_prod_val = float(sub["production"].sum()) if ("production" in sub.columns and records > 0) else 0.0
dist_cnt = int(sub["district"].nunique()) if ("district" in sub.columns and records > 0) else 0

# --- KPI Cards ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Records", f"{records:,}")
k2.metric("Avg yield (tonnes/ha)", f"{avg_yield_val:.2f}")
k3.metric("Total production", f"{tot_prod_val:,.0f}")
k4.metric("Districts", f"{dist_cnt:,}")

# --- Two Charts Side-by-Side ---
left_col, right_col = st.columns([1, 1.25])

with left_col:
    crop_label = sel_crop if sel_crop != "All" else "All Crops"
    st.subheader(f"{crop_label}: average yield by year")
    if records > 0 and "year" in sub.columns and "yield" in sub.columns:
        yearly_yield = (
            sub.groupby("year", as_index=False, observed=True)["yield"]
            .mean()
            .sort_values("year")
        )
        fig_yr = px.line(yearly_yield, x="year", y="yield", markers=True)
        fig_yr.update_traces(line=dict(color="#111111", width=2), marker=dict(color="#111111", size=6))
        fig_yr.update_layout(
            margin=dict(l=55, r=20, t=20, b=45),
            xaxis_title="year",
            yaxis_title="yield",
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_yr, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with right_col:
    st.subheader("Top 10 districts by yield")
    if records > 0 and "district" in sub.columns and "yield" in sub.columns:
        grp_cols = ["district", "state"] if "state" in sub.columns else ["district"]
        top_dist = (
            sub.groupby(grp_cols, as_index=False, observed=True)["yield"]
            .mean()
            .dropna(subset=["yield"])
            .sort_values("yield", ascending=False)
            .head(10)
        )
        if "state" in top_dist.columns:
            top_dist["district_label"] = top_dist["district"].astype(str) + " (" + top_dist["state"].astype(str) + ")"
        else:
            top_dist["district_label"] = top_dist["district"].astype(str)

        top_dist = top_dist.sort_values("yield", ascending=True)
        fig_dist = px.bar(
            top_dist,
            x="yield",
            y="district_label",
            orientation="h"
        )
        fig_dist.update_traces(marker_color="#111111")
        fig_dist.update_layout(
            margin=dict(l=220, r=25, t=20, b=45),
            xaxis_title="yield",
            yaxis_title="",
            yaxis=dict(automargin=True, tickfont=dict(size=11)),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.info("No district data available for selected filters.")

# --- Sidebar: Yield Predictor (Lazy model load only when button clicked) ---
st.sidebar.header("Crop Yield Predictor")
if MODEL_PATH.exists():
    feat_choices = ["state", "district", "crop", "season"]
    p_state = st.sidebar.selectbox("Predict State", sorted(df["state"].dropna().unique().tolist()), key="p_state") if "state" in df.columns else None
    d_pool = df.loc[df["state"] == p_state, "district"] if ("state" in df.columns and "district" in df.columns and p_state is not None) else df.get("district")
    p_dist = st.sidebar.selectbox("Predict District", sorted(d_pool.dropna().unique().tolist()), key="p_dist") if d_pool is not None else None
    p_crop = st.sidebar.selectbox("Predict Crop", sorted(df["crop"].dropna().unique().tolist()), key="p_crop") if "crop" in df.columns else None
    p_season = st.sidebar.selectbox("Predict Season", sorted(df["season"].dropna().unique().tolist()), key="p_season") if "season" in df.columns else None
    p_year = st.sidebar.number_input("Predict Year", min_value=1997, max_value=2026, value=2020, key="p_year")
    p_area = st.sidebar.number_input("Predict Area (ha)", min_value=0.1, value=100.0, key="p_area")

    if st.sidebar.button("Predict Yield"):
        model = load_model(MODEL_PATH)
        feat_names = list(getattr(model, "feature_names_in_", []))
        row = {"year": float(p_year), "area": float(p_area)}

        mapping = {
            "state_encoded": ("state", p_state),
            "district_encoded": ("district", p_dist),
            "crop_encoded": ("crop", p_crop),
            "season_encoded": ("season", p_season),
        }
        for enc_col, (raw_col, val) in mapping.items():
            if enc_col in feat_names and raw_col in df.columns and enc_col in df.columns and val is not None:
                match = df.loc[df[raw_col] == val, enc_col]
                if not match.empty:
                    row[enc_col] = float(match.iloc[0])

        for col in feat_names:
            if col not in row and col in df.columns:
                row[col] = float(df[col].median())

        if feat_names:
            X_pred = pd.DataFrame([row])[feat_names]
            pred_out = float(model.predict(X_pred)[0])
            st.sidebar.success(f"Predicted Yield: **{pred_out:.2f}**")
else:
    st.sidebar.info("Saved model not found.")

mandi_top = load_mandi_top(DB_PATH)
if not mandi_top.empty:
    with st.expander("Mandi Prices (SQLite: mandi_prices)"):
        st.dataframe(mandi_top, use_container_width=True)