import pandas as pd
import sqlite3
import os

# 1. Connect to database
db_path = os.path.join("agriculture.db")
conn = sqlite3.connect(db_path)

print("--- Advanced SQL Analytics for TripleStack Project ---")

# Query 1: Average Production Value by Unit Type
query_avg = """
SELECT unit, ROUND(AVG(production_value), 2) as avg_production
FROM crop_trends
GROUP BY unit
ORDER BY avg_production DESC;
"""
print("\n1. Average Production by Unit:")
print(pd.read_sql(query_avg, conn))

# Query 2: Trend for Foodgrains Production over the Years
query_trend = """
SELECT year, production_value 
FROM crop_trends 
WHERE particulars LIKE '%Foodgrains%' AND unit = 'Ton mn'
ORDER BY year ASC;
"""
print("\n2. Foodgrains Production Trend (Ton mn):")
print(pd.read_sql(query_trend, conn).head(10))

conn.close()