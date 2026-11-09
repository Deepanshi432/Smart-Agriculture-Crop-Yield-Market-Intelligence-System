"""STEP 1 - Clean the district-wise crop production data.
Input : data/raw/Crop_Production_Statistics.csv
Output: data/processed/cleaned_crop_data.csv
"""
import pandas as pd
from config import find_raw, PROCESSED, clean_text

df = pd.read_csv(find_raw("Crop_Production_Statistics*.csv"))
n0 = len(df)
print(f"Loaded {n0:,} rows")

# 1. Column names + text values: strip spaces, collapse double spaces
df.columns = df.columns.str.strip().str.lower()
df = df.rename(columns={"crop_year": "year"})
for c in ["state", "district", "crop", "season"]:
    df[c] = clean_text(df[c]).str.title()

# 2. Standardise state names (one name per state/UT)
df["state"] = df["state"].replace({
    "The Dadra And Nagar Haveli": "Dadra And Nagar Haveli",
    "Andaman And Nicobar Island": "Andaman And Nicobar Islands",
    "Laddak": "Ladakh",
})

# 3. Missing / invalid values.
#    Missing Production is NOT a crop failure and cannot be rebuilt from Area*Yield
#    (Yield is 0 on exactly those rows), so we drop them. Zero production is dropped
#    too: in this dataset it mostly means "not reported".
df = df.dropna(subset=["crop", "area", "production"])
df = df[(df["area"] > 0) & (df["production"] > 0)]
print(f"After dropping missing/zero Area or Production: {len(df):,}")

# 4. Recompute Yield = Production / Area
df["yield"] = df["production"] / df["area"]

# 5. Remove duplicate records
before = len(df)
df = df.drop_duplicates(subset=["state", "district", "crop", "year", "season"])
print(f"Removed {before - len(df):,} duplicates")

# 6. Outliers: per-crop IQR rule (units differ by crop, so never use one global cut-off)
q1 = df.groupby("crop")["yield"].transform(lambda s: s.quantile(0.25))
q3 = df.groupby("crop")["yield"].transform(lambda s: s.quantile(0.75))
before = len(df)
df = df[df["yield"] <= q3 + 3 * (q3 - q1)]
print(f"Removed {before - len(df):,} yield outliers")

# 7. Flag crops whose yield is not in tonnes/ha (compare these only within the same crop)
df["yield_unit_note"] = df["crop"].map(
    lambda c: "nuts/ha" if c == "Coconut" else "tonnes/ha")

df = df[["state", "district", "crop", "year", "season", "area", "production", "yield", "yield_unit_note"]]
out = PROCESSED / "cleaned_crop_data.csv"
df.to_csv(out, index=False)
print(f"Saved {len(df):,} rows ({len(df)/n0:.1%} kept) -> {out}")
