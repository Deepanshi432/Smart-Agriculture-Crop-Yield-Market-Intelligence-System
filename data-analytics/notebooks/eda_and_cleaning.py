import pandas as pd
import numpy as np
import os

# 1. Define file path and name (Using CSV format)
file_name = "crop_production.csv"
file_path = os.path.join("..", "data", "raw", file_name)

print(f"Loading dataset from {file_path}...")

# 2. Load the dataset using pd.read_csv
try:
    df = pd.read_csv(file_path)
    print("✅ Dataset loaded successfully!")
except Exception as e:
    print(f"❌ Error loading file: {e}")
    exit()

# 3. Inspect basic info
print("\n--- Dataset Info ---")
print(df.info())

print("\n--- First 3 Rows ---")
print(df.head(3))

print("\n--- Missing Values Count ---")
print(df.isnull().sum())

# 4. Clean column names (convert to lowercase and strip whitespace)
df.columns = df.columns.str.strip().str.lower()
print("\nCleaned Column Names:", list(df.columns))

# 5. Handle Missing Values
if 'production' in df.columns:
    df = df.dropna(subset=['production'])

if 'area' in df.columns:
    df = df.dropna(subset=['area'])
    # Remove rows where area is 0 or negative to avoid division by zero errors
    df = df[df['area'] > 0]

# 6. Feature Engineering: Calculate Yield
# Yield = Production / Area
if 'production' in df.columns and 'area' in df.columns:
    df['yield'] = df['production'] / df['area']
    print("\n--- Yield Statistics ---")
    print(df['yield'].describe())

# 7. Save the processed clean dataset
output_dir = os.path.join("..", "data", "processed")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "cleaned_crop_data.csv")
df.to_csv(output_path, index=False)

print(f"\n✅ Cleaned dataset successfully saved to: {output_path}")