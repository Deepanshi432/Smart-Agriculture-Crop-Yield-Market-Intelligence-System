import pandas as pd
import numpy as np
import os

RAW = os.path.join("..", "data", "raw", "Crop_Production_Statistics.csv")
OUT = os.path.join("..", "data", "processed", "cleaned_crop_data.csv")

df = pd.read_csv(RAW)
n0 = len(df)
print(f"Loaded: {n0:,} rows")

# 1. Strip spaces from column names and text values
df.columns = df.columns.str.strip().str.lower()
for c in df.select_dtypes(include="object").columns:
    df[c] = df[c].str.strip()
df = df.rename(columns={"crop_year": "year"})

# 2. Standardize state names
df["state"] = df["state"].str.title()
df["state"] = df["state"].replace({
    "The Dadra And Nagar Haveli": "Dadra And Nagar Haveli",
    "Andaman And Nicobar Island": "Andaman And Nicobar Islands",
    "Laddak": "Ladakh",
})
df["district"] = df["district"].str.title()
df["crop"] = df["crop"].str.title()

# 3. Missing / invalid values
df = df.dropna(subset=["crop", "production", "area"])
df = df[(df["area"] > 0) & (df["production"] > 0)]
print(f"After removing missing/zero Area or Production: {len(df):,}")

# 4. Recompute yield (production / area) so it's consistent
df["yield"] = df["production"] / df["area"]

# 5. Remove duplicates
df = df.drop_duplicates(subset=["state", "district", "crop", "year", "season"])

# 6. Outliers: per-crop IQR rule (Q3 + 3*IQR), because crops have different units
q1 = df.groupby("crop")["yield"].transform(lambda s: s.quantile(0.25))
q3 = df.groupby("crop")["yield"].transform(lambda s: s.quantile(0.75))
upper = q3 + 3 * (q3 - q1)
before = len(df)
df = df[df["yield"] <= upper]
print(f"Removed {before - len(df):,} yield outliers")

# 7. Crops whose yield is not comparable with others (production not in tonnes)
med = df.groupby("crop")["yield"].median()
print("\nCrops with median yield > 10 (different unit, compare only within crop):")
print(med[med > 10].round(1).sort_values(ascending=False))

df = df[["state", "district", "crop", "year", "season", "area", "production", "yield"]]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
df.to_csv(OUT, index=False)
print(f"\nSaved {len(df):,} rows -> {OUT}  (kept {len(df)/n0:.1%})")
print(df.describe().round(2))