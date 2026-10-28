"""
BuyWise - Data Inspector
Author: Nandini Singh
Description:
Reads all CSV files from data/raw and prints
basic information for data understanding.
"""

from pathlib import Path
import pandas as pd

# ----------------------------
# Dataset Folder
# ----------------------------

DATA_DIR = Path("data/raw")

# ----------------------------
# Read all CSV files
# ----------------------------

csv_files = list(DATA_DIR.glob("*.csv"))

print("=" * 80)
print(f"BUYWISE DATA INSPECTOR")
print("=" * 80)

print(f"\nFound {len(csv_files)} CSV files.\n")

# ----------------------------
# Inspect each dataset
# ----------------------------

for file in csv_files:

    print("=" * 80)
    print(f"Dataset : {file.name}")

    try:

        df = pd.read_csv(file)

        print(f"Rows    : {df.shape[0]:,}")
        print(f"Columns : {df.shape[1]}")

        print("\nColumn Names")
        print("-" * 50)

        for col in df.columns:
            print(col)

        print("\nMissing Values")
        print("-" * 50)
        print(df.isnull().sum())

        print("\nData Types")
        print("-" * 50)
        print(df.dtypes)

        print("\nFirst Five Records")
        print("-" * 50)
        print(df.head())

    except Exception as e:

        print(f"Error reading {file.name}")
        print(e)

    print("\n")