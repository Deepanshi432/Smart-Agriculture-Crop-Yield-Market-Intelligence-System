import pandas as pd
import sqlite3
import os

# 1. Define paths
db_path = os.path.join("..", "sql", "agriculture.db")
csv_path = os.path.join("..", "data", "processed", "melted_crop_trends.csv")

# 2. Connect to SQLite database (creates 'agriculture.db' automatically)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 3. Load melted CSV into a SQL table named 'crop_trends'
print("Loading melted data into SQLite database...")
df = pd.read_csv(csv_path)
df.to_sql('crop_trends', conn, if_exists='replace', index=False)
print("✅ Table 'crop_trends' created successfully in agriculture.db!")

# 4. Run sample SQL queries to demonstrate analytics
print("\n--- SQL Query 1: Top 5 Records by Production Value ---")
query_1 = """
SELECT particulars, unit, year, production_value 
FROM crop_trends 
WHERE production_value > 0 
ORDER BY production_value DESC 
LIMIT 5;
"""
print(pd.read_sql(query_1, conn))

print("\n--- SQL Query 2: Summary Count by Unit Type ---")
query_2 = """
SELECT unit, COUNT(*) as record_count 
FROM crop_trends 
GROUP BY unit;
"""
print(pd.read_sql(query_2, conn))

# Close connection
conn.close()