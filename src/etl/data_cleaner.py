"""
BuyWise Data Cleaning
"""

import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

PROCESSED.mkdir(exist_ok=True)

for file in RAW.glob("*.csv"):

    print(f"Cleaning {file.name}")

    df = pd.read_csv(file)

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Remove empty rows
    df = df.dropna(how="all")

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    output = PROCESSED / file.name

    df.to_csv(output, index=False)

    print(f"Saved -> {output.name}")

print("\nCleaning Completed Successfully.")