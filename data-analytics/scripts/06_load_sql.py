"""STEP 6 - Load processed CSVs into SQLite and run the business queries in sql/queries.sql.
Output: sql/agriculture.db   (tables: crop_yield, rainfall, merged_yield, mandi_prices)
"""
import sqlite3
import pandas as pd
from config import PROCESSED, DB_PATH, SQL_DIR

conn = sqlite3.connect(DB_PATH)
for table, f in [("crop_yield", "cleaned_crop_data.csv"),
                 ("rainfall", "cleaned_rainfall.csv"),
                 ("merged_yield", "merged_yield_data.csv"),
                 ("mandi_prices", "cleaned_mandi_prices.csv")]:
    pd.read_csv(PROCESSED / f).to_sql(table, conn, if_exists="replace", index=False)
    print(f"loaded {table}")

conn.execute("CREATE INDEX IF NOT EXISTS ix_cy ON crop_yield(state, crop, year)")
conn.execute("CREATE INDEX IF NOT EXISTS ix_my ON merged_yield(crop, season)")

sql = (SQL_DIR / "queries.sql").read_text()
queries = [q.strip() for q in sql.split(";") if "SELECT" in q or "WITH" in q]
pd.set_option("display.width", 140)
for i, q in enumerate(queries, 1):
    title = next((l.replace("--", "").strip() for l in q.splitlines() if l.startswith("-- Q")), f"Query {i}")
    print(f"\n=== {title}")
    q = "\n".join(l for l in q.splitlines() if not l.strip().startswith("--"))
    print(pd.read_sql(q, conn).head(12).to_string(index=False))
conn.close()
