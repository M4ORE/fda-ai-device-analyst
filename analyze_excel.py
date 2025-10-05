import pandas as pd
import json
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Read Excel file
df = pd.read_excel('ai-ml-enabled-devices-excel.xlsx')

# Show basic info
print("=== EXCEL STRUCTURE ===")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print("\n=== COLUMNS ===")
print(df.columns.tolist())
print("\n=== FIRST 3 ROWS ===")
print(df.head(3).to_string())
print("\n=== DATA TYPES ===")
print(df.dtypes)
print("\n=== NULL VALUES ===")
print(df.isnull().sum())
print("\n=== SAMPLE DATA (JSON) ===")
print(json.dumps(df.head(2).to_dict(orient='records'), indent=2, default=str))
