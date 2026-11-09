"""STEP 3 - Merge crop data with rainfall (this table is the input for the ML model).
Input : cleaned_crop_data.csv + cleaned_rainfall.csv
Output: data/processed/merged_yield_data.csv
"""
import pandas as pd
from config import PROCESSED

crop = pd.read_csv(PROCESSED / "cleaned_crop_data.csv")
rain = pd.read_csv(PROCESSED / "cleaned_rainfall.csv")

m = crop.merge(rain, on=["state", "year"], how="left")
print(f"Rows without rainfall (state-year not in IMD data): {m['annual'].isna().sum():,}")
m = m.dropna(subset=["annual"])

# Season-specific rainfall: the rainfall that matters most for that season
def season_rain(row):
    if row["season"] == "Kharif":
        return row["jjas"]                    # monsoon Jun-Sep
    if row["season"] == "Rabi":
        return row["ond"] + row["jf"]         # Oct-Dec + Jan-Feb
    if row["season"] == "Summer":
        return row["mam"]                     # Mar-May
    return row["annual"]                      # Whole Year / Autumn / Winter

m["season_rainfall"] = m.apply(season_rain, axis=1).round(1)

out = PROCESSED / "merged_yield_data.csv"
m.to_csv(out, index=False)
print(f"Saved {len(m):,} rows, years {m['year'].min()}-{m['year'].max()} -> {out}")
