import sqlite3
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Crop Yield & Market Intelligence | Smart Agriculture",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Deep midnight-indigo & vibrant neon-accent theme inspired by reference UI
st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at 12% 10%, rgba(124, 58, 237, 0.24), transparent 36%),
                        radial-gradient(circle at 88% 18%, rgba(236, 72, 153, 0.20), transparent 38%),
                        radial-gradient(circle at 55% 88%, rgba(6, 182, 212, 0.16), transparent 42%),
                        linear-gradient(145deg, #0d0b1e 0%, #15102b 52%, #1b1236 100%);
            color: #f3f0ff;
        }
        .block-container {
            padding-top: 2.3rem;
            padding-bottom: 2.5rem;
            max-width: 1320px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #120e26 0%, #191334 100%);
            border-right: 1px solid rgba(167, 139, 250, 0.22);
        }
        [data-testid="stSidebar"] * {
            color: #ede9fe;
        }
        .hero-banner {
            background: linear-gradient(120deg, rgba(30, 23, 62, 0.88), rgba(45, 22, 78, 0.82));
            border: 1px solid rgba(192, 132, 252, 0.28);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 12px 32px rgba(5, 3, 18, 0.45);
        }
        .hero-title {
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.25;
            background: linear-gradient(90deg, #ffffff 0%, #67e8f9 50%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 0.3rem 0;
        }
        .hero-sub {
            font-size: 0.9rem;
            color: #c4b5fd;
            margin: 0;
        }
        .kpi-card {
            border-radius: 14px;
            padding: 1rem 1.15rem;
            border: 1px solid rgba(255, 255, 255, 0.14);
            box-shadow: 0 10px 24px rgba(6, 4, 20, 0.35);
        }
        .kpi-cyan {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.28), rgba(37, 99, 235, 0.22));
            border-color: rgba(34, 211, 238, 0.45);
        }
        .kpi-pink {
            background: linear-gradient(135deg, rgba(236, 72, 153, 0.28), rgba(147, 51, 234, 0.24));
            border-color: rgba(244, 114, 182, 0.45);
        }
        .kpi-violet {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.30), rgba(79, 70, 229, 0.22));
            border-color: rgba(167, 139, 250, 0.45);
        }
        .kpi-amber {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.26), rgba(236, 72, 153, 0.20));
            border-color: rgba(251, 191, 36, 0.45);
        }
        .kpi-label {
            font-size: 0.74rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #e9d5ff;
            margin-bottom: 0.35rem;
        }
        .kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.2;
        }
        .kpi-sub {
            font-size: 0.76rem;
            color: #ddd6fe;
            margin-top: 0.25rem;
        }
        .pred-card {
            background: linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(236, 72, 153, 0.18));
            border: 1px solid rgba(103, 232, 249, 0.45);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-top: 0.8rem;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            color: #c4b5fd;
            font-weight: 600;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #06b6d4 0%, #a855f7 55%, #ec4899 100%);
            border: none;
            color: #ffffff;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Resolve paths reliably across execution contexts
APP_DIR = Path(__file__).resolve().parent
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
    frame = pd.read_csv(csv_path)
    frame.columns = frame.columns.str.strip()
    return frame


@st.cache_resource
def load_model(model_path: Path):
    return joblib.load(model_path)


if PROCESSED_CSV is None:
    expected_csv = APP_DIR / "data" / "processed" / "processed_crop_data.csv"
    st.error(f"Processed CSV not found at: {expected_csv}")
    st.stop()

df = load_data(PROCESSED_CSV)
model = load_model(MODEL_PATH) if MODEL_PATH is not None else None

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

# --- Header Banner ---
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">Smart Agriculture: Crop Yield & Market Intelligence</div>
        <div class="hero-sub">Vibrant multi-dimensional analytics for crop production, yield forecasting, and mandi price intelligence</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Colorful KPI Strip ---
total_records = f"{len(df):,}"
states_cnt = f"{df[state_col].nunique()}" if state_col else "—"
crops_cnt = f"{df[crop_col].nunique()}" if crop_col else "—"
avg_yield_val = f"{df[yield_col].mean():.2f}" if yield_col else "—"
year_span = (
    f"{int(df[year_col].min())}–{int(df[year_col].max())}"
    if year_col and pd.api.types.is_numeric_dtype(df[year_col])
    else "Historical dataset"
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f"""<div class="kpi-card kpi-cyan">
            <div class="kpi-label">Total Records</div>
            <div class="kpi-value">{total_records}</div>
            <div class="kpi-sub">Span: {year_span}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""<div class="kpi-card kpi-pink">
            <div class="kpi-label">States / UTs</div>
            <div class="kpi-value">{states_cnt}</div>
            <div class="kpi-sub">Standardized regions</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"""<div class="kpi-card kpi-violet">
            <div class="kpi-label">Crops Tracked</div>
            <div class="kpi-value">{crops_cnt}</div>
            <div class="kpi-sub">Active crop varieties</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"""<div class="kpi-card kpi-amber">
            <div class="kpi-label">Average Yield</div>
            <div class="kpi-value">{avg_yield_val}</div>
            <div class="kpi-sub">Dataset mean yield</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.write("")

# --- Sidebar: Yield Predictor ---
st.sidebar.markdown("### 🌱 Crop Yield Predictor")
st.sidebar.caption("Choose location, crop, season, and area to forecast yield.")

if model is None:
    st.sidebar.info("Yield model file (`crop_yield_model.pkl`) is not present locally.")
else:
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

    if st.sidebar.button("Predict Yield", type="primary", use_container_width=True):
        missing_feats = [f for f in model_features if f not in input_values]
        if missing_feats:
            st.sidebar.error(f"Missing features: {missing_feats}")
        else:
            X_input = pd.DataFrame([input_values])[model_features]
            pred_yield = float(model.predict(X_input)[0])
            st.sidebar.markdown(
                f"""<div class="pred-card">
                    <div style="font-size:0.75rem; color:#67e8f9; text-transform:uppercase; letter-spacing:0.05em;">Predicted Yield</div>
                    <div style="font-size:1.45rem; font-weight:700; color:#ffffff;">{pred_yield:.2f}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def make_colorful_bar_chart(
    data: pd.DataFrame, x_col: str, y_col: str, title: str, palette: list[str]
):
    chart = (
        alt.Chart(data, title=alt.TitleParams(text=title, color="#f5f3ff", fontSize=15))
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(
                f"{x_col}:N",
                sort="-y",
                axis=alt.Axis(
                    labelAngle=-35,
                    title=None,
                    labelColor="#ddd6fe",
                    domainColor="rgba(196, 181, 253, 0.3)",
                    tickColor="rgba(196, 181, 253, 0.3)",
                    labelLimit=145,
                ),
            ),
            y=alt.Y(
                f"{y_col}:Q",
                title="Total Production",
                axis=alt.Axis(
                    labelColor="#ddd6fe",
                    titleColor="#c4b5fd",
                    gridColor="rgba(196, 181, 253, 0.12)",
                    domainColor="rgba(196, 181, 253, 0.3)",
                ),
            ),
            color=alt.Color(
                f"{x_col}:N",
                sort="-y",
                scale=alt.Scale(range=palette),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col.title()),
                alt.Tooltip(f"{y_col}:Q", title="Production", format=",.0f"),
            ],
        )
        .properties(height=350)
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
    )
    return chart


# --- Main Tabs ---
tab1, tab2 = st.tabs(["📊 Production & Yield Insights", "🏪 Mandi Prices (SQL)"])

with tab1:
    st.write("")
    left, right = st.columns(2, gap="large")

    crop_palette = [
        "#22d3ee", "#38bdf8", "#818cf8", "#a855f7", "#d946ef",
        "#ec4899", "#f43f5e", "#fb923c", "#facc15", "#34d399",
    ]
    state_palette = [
        "#ec4899", "#d946ef", "#a855f7", "#8b5cf6", "#6366f1",
        "#3b82f6", "#06b6d4", "#14b8a6", "#f59e0b", "#f97316",
    ]

    if crop_col and prod_col:
        with left:
            top_crops = (
                df.groupby(crop_col, as_index=False)[prod_col]
                .sum()
                .sort_values(prod_col, ascending=False)
                .head(10)
            )
            st.altair_chart(
                make_colorful_bar_chart(
                    top_crops,
                    crop_col,
                    prod_col,
                    "Top 10 Crops by Total Production",
                    crop_palette,
                ),
                use_container_width=True,
            )
    else:
        with left:
            st.info("Crop or Production columns not found in dataset.")

    if state_col and prod_col:
        with right:
            top_states = (
                df.groupby(state_col, as_index=False)[prod_col]
                .sum()
                .sort_values(prod_col, ascending=False)
                .head(10)
            )
            st.altair_chart(
                make_colorful_bar_chart(
                    top_states,
                    state_col,
                    prod_col,
                    "Top 10 States by Total Production",
                    state_palette,
                ),
                use_container_width=True,
            )
    else:
        with right:
            st.info("State or Production columns not found in dataset.")

with tab2:
    st.write("")
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
                    SELECT
                        commodity AS Commodity,
                        ROUND(AVG(modal_price), 2) AS Avg_Modal_Price,
                        COUNT(*) AS Market_Entries
                    FROM mandi_prices
                    GROUP BY commodity
                    HAVING Market_Entries >= 20
                    ORDER BY Avg_Modal_Price DESC
                    LIMIT 25
                    """,
                    conn,
                )
                search_q = st.text_input(
                    "Filter commodity",
                    placeholder="Type commodity name (e.g., Rice, Wheat, Potato)...",
                )
                if search_q.strip():
                    mandi_df = mandi_df[
                        mandi_df["Commodity"]
                        .astype(str)
                        .str.contains(search_q.strip(), case=False, na=False)
                    ]

                st.dataframe(
                    mandi_df.head(10),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("`mandi_prices` table not found in `agriculture.db`.")
            conn.close()
        except Exception as exc:
            st.warning(f"Could not query `agriculture.db`: {exc}")