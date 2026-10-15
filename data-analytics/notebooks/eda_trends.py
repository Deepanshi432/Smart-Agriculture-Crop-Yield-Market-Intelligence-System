import pandas as pd
import os

# 1. Load the cleaned dataset
file_path = os.path.join("..", "data", "processed", "cleaned_crop_data.csv")
df = pd.read_csv(file_path)

print("--- Cleaned Dataset Overview ---")
print(f"Total rows (Particulars): {len(df)}")
print(df[['particulars', 'unit']].head())

# 2. Reshape (Melt) the dataset from Wide to Long format for easier analysis & SQL
# This turns year columns into rows so we can query trends easily
year_cols = [col for col in df.columns if '-' in col or col.isdigit()]

df_melted = pd.melt(
    df, 
    id_vars=['particulars', 'frequency', 'unit'], 
    value_vars=year_cols,
    var_name='year', 
    value_name='production_value'
)

# Clean year format (e.g., '3-2005' -> '2005')
df_melted['year'] = df_melted['year'].str.replace('3-', '')

# Drop rows with missing production values
df_melted = df_melted.dropna(subset=['production_value'])

# Save melted version for SQL and Power BI
output_path = os.path.join("..", "data", "processed", "melted_crop_trends.csv")
df_melted.to_csv(output_path, index=False)

print(f"\n✅ Reshaped time-series data saved to: {output_path}")
print("\n--- Sample Melted Data ---")
print(df_melted.head(5))    