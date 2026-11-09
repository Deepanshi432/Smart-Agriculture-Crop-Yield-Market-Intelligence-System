"""STEP 4 - Clean mandi (market) prices.
Input : data/raw/mandi_prices.csv
Output: data/processed/cleaned_mandi_prices.csv
NOTE  : this file is a one-day snapshot, so it supports price COMPARISON, not price TRENDS.
"""
import pandas as pd
from config import find_raw, PROCESSED, clean_text

m = pd.read_csv(find_raw("mandi_prices*.csv"))
m.columns = (m.columns.str.replace("_x0020_", "_", regex=False)
                       .str.strip().str.lower())
m = m.rename(columns={"arrival_date": "date"})
for c in ["state", "district", "market", "commodity", "variety", "grade"]:
    m[c] = clean_text(m[c]).str.title()

m["date"] = pd.to_datetime(m["date"], format="%d/%m/%Y", errors="coerce")
m = m.dropna(subset=["date", "modal_price"])
m = m[(m["min_price"] > 0) & (m["max_price"] >= m["min_price"])]
m = m.drop_duplicates()

out = PROCESSED / "cleaned_mandi_prices.csv"
m.to_csv(out, index=False)
print(f"Saved {len(m):,} rows, {m['commodity'].nunique()} commodities, "
      f"dates: {m['date'].dt.date.nunique()} day(s) -> {out}")
