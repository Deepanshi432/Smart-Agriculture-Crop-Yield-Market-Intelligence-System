"""STEP 2 - Clean IMD rainfall and convert sub-division rainfall to STATE-level rainfall.
Input : data/raw/Sub_Division_IMD_2017.csv
Output: data/processed/cleaned_rainfall.csv   (state, year, jf, mam, jjas, ond, annual)
"""
import pandas as pd
from config import find_raw, PROCESSED

r = pd.read_csv(find_raw("Sub_Division_IMD_2017*.csv"))
r.columns = r.columns.str.strip().str.lower()
r["subdivision"] = r["subdivision"].str.strip()

months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

# 1. Fill missing monthly values with that sub-division's median for the same month
for m in months:
    r[m] = r[m].fillna(r.groupby("subdivision")[m].transform("median"))

# 2. Rebuild the totals from the (now complete) months so they are always consistent
r["jf"] = r[["jan", "feb"]].sum(axis=1)
r["mam"] = r[["mar", "apr", "may"]].sum(axis=1)
r["jjas"] = r[["jun", "jul", "aug", "sep"]].sum(axis=1)       # monsoon -> Kharif
r["ond"] = r[["oct", "nov", "dec"]].sum(axis=1)               # post-monsoon -> Rabi
r["annual"] = r[months].sum(axis=1)

# 3. IMD sub-division -> crop-data state. Where a state has several sub-divisions we average them.
S = {
    "Andaman And Nicobar Islands": ["Andaman & Nicobar Islands"],
    "Arunachal Pradesh": ["Arunachal Pradesh"],
    "Assam": ["Assam & Meghalaya"],
    "Meghalaya": ["Assam & Meghalaya"],
    "Nagaland": ["Naga Mani Mizo Tripura"],
    "Manipur": ["Naga Mani Mizo Tripura"],
    "Mizoram": ["Naga Mani Mizo Tripura"],
    "Tripura": ["Naga Mani Mizo Tripura"],
    "West Bengal": ["Sub Himalayan West Bengal & Sikkim", "Gangetic West Bengal"],
    "Sikkim": ["Sub Himalayan West Bengal & Sikkim"],
    "Odisha": ["Orissa"],
    "Jharkhand": ["Jharkhand"],
    "Bihar": ["Bihar"],
    "Uttar Pradesh": ["East Uttar Pradesh", "West Uttar Pradesh"],
    "Uttarakhand": ["Uttarakhand"],
    "Haryana": ["Haryana Delhi & Chandigarh"],
    "Delhi": ["Haryana Delhi & Chandigarh"],
    "Chandigarh": ["Haryana Delhi & Chandigarh"],
    "Punjab": ["Punjab"],
    "Himachal Pradesh": ["Himachal Pradesh"],
    "Jammu And Kashmir": ["Jammu & Kashmir"],
    "Ladakh": ["Jammu & Kashmir"],
    "Rajasthan": ["West Rajasthan", "East Rajasthan"],
    "Madhya Pradesh": ["West Madhya Pradesh", "East Madhya Pradesh"],
    "Chhattisgarh": ["Chhattisgarh"],
    "Gujarat": ["Gujarat Region", "Saurashtra & Kutch"],
    "Dadra And Nagar Haveli": ["Gujarat Region"],
    "Daman And Diu": ["Gujarat Region"],
    "Goa": ["Konkan & Goa"],
    "Maharashtra": ["Konkan & Goa", "Madhya Maharashtra", "Matathwada", "Vidarbha"],
    "Andhra Pradesh": ["Coastal Andhra Pradesh", "Rayalseema"],
    "Telangana": ["Telangana"],
    "Karnataka": ["Coastal Karnataka", "North Interior Karnataka", "South Interior Karnataka"],
    "Kerala": ["Kerala"],
    "Tamil Nadu": ["Tamil Nadu"],
    "Puducherry": ["Tamil Nadu"],
}

cols = ["jf", "mam", "jjas", "ond", "annual"]
parts = []
for state, subs in S.items():
    t = r[r["subdivision"].isin(subs)].groupby("year")[cols].mean().reset_index()
    t.insert(0, "state", state)
    parts.append(t)
out_df = pd.concat(parts, ignore_index=True).round(1)

out = PROCESSED / "cleaned_rainfall.csv"
out_df.to_csv(out, index=False)
print(f"Saved {len(out_df):,} rows, {out_df['state'].nunique()} states, "
      f"years {out_df['year'].min()}-{out_df['year'].max()} -> {out}")
