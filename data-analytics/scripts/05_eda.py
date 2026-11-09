"""STEP 5 - Exploratory Data Analysis. Saves interactive Plotly charts to dashboard/charts/*.html
Input : data/processed/merged_yield_data.csv, cleaned_crop_data.csv
"""
import pandas as pd
import plotly.express as px
from config import PROCESSED, CHARTS

df = pd.read_csv(PROCESSED / "cleaned_crop_data.csv")
mg = pd.read_csv(PROCESSED / "merged_yield_data.csv")

def save(fig, name):
    fig.write_html(CHARTS / f"{name}.html", include_plotlyjs="cdn")
    print("saved", name)

# 1. Top 10 producing states for Rice (compare states only within ONE crop)
rice = df[df.crop == "Rice"].groupby("state")["production"].sum().nlargest(10).reset_index()
save(px.bar(rice, x="production", y="state", orientation="h",
            title="Top 10 Rice-producing states (total production, 1997-2020)")
     .update_layout(yaxis={"categoryorder": "total ascending"}), "01_top_states_rice")

# 2. Yield trend of major crops over the years (national average, same crop over time)
major = ["Rice", "Wheat", "Maize", "Sugarcane", "Potato"]
t = df[df.crop.isin(major)].groupby(["year", "crop"])["yield"].mean().reset_index()
save(px.line(t, x="year", y="yield", color="crop", markers=True,
             title="Average yield trend of major crops"), "02_yield_trend")

# 3. Season-wise performance: total area and production
s = df.groupby("season").agg(area=("area", "sum"), n=("crop", "size")).reset_index()
save(px.bar(s, x="season", y="area", text="n",
            title="Season-wise cultivated area (label = number of records)"), "03_season_area")

# 4. Heatmap: Wheat yield by state and year
w = df[df.crop == "Wheat"].groupby(["state", "year"])["yield"].mean().unstack()
save(px.imshow(w, aspect="auto", color_continuous_scale="YlGn",
               title="Wheat yield heatmap (state x year)"), "04_heatmap_wheat_yield")

# 5. Rainfall vs yield (Rice, Kharif): does monsoon rain relate to yield?
r = mg[(mg.crop == "Rice") & (mg.season == "Kharif")].groupby(["state", "year"]).agg(
    yield_=("yield", "mean"), rain=("season_rainfall", "mean")).reset_index()
save(px.scatter(r, x="rain", y="yield_", color="state", opacity=0.6,
                title="Kharif rice: monsoon rainfall (mm) vs yield",
                labels={"rain": "Monsoon rainfall (mm)", "yield_": "Yield (t/ha)"}),
     "05_rainfall_vs_yield")

# 6. Top 10 districts by Rice yield (latest 5 years)
latest = df[(df.crop == "Rice") & (df.year >= df.year.max() - 4)]
d = latest.groupby(["state", "district"])["yield"].mean().nlargest(10).reset_index()
d["label"] = d["district"] + " (" + d["state"] + ")"
save(px.bar(d, x="yield", y="label", orientation="h",
            title="Top 10 districts by Rice yield (last 5 years)")
     .update_layout(yaxis={"categoryorder": "total ascending"}), "06_top_districts_rice")

# Correlation numbers
print("\nCorrelation of season rainfall with yield per crop (top crops):")
for c in ["Rice", "Wheat", "Maize"]:
    x = mg[mg.crop == c]
    print(f"  {c}: {x['season_rainfall'].corr(x['yield']):.3f}")
