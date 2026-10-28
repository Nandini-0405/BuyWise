"""
BuyWise
Category Intelligence Engine
"""

import sqlite3
import pandas as pd

# ==========================================
# Connect Database
# ==========================================

DATABASE = "database/buywise.db"

conn = sqlite3.connect(DATABASE)

df = pd.read_sql("SELECT * FROM products", conn)

conn.close()

print("=" * 70)
print("BUYWISE - CATEGORY ANALYSIS")
print("=" * 70)

# ==========================================
# Clean Price Columns
# ==========================================

df["discounted_price"] = (
    df["discounted_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
)

df["actual_price"] = (
    df["actual_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
)

# Convert to numeric

df["discounted_price"] = pd.to_numeric(
    df["discounted_price"],
    errors="coerce"
)

df["actual_price"] = pd.to_numeric(
    df["actual_price"],
    errors="coerce"
)

# ==========================================
# Clean Discount
# ==========================================

df["discount_percentage"] = (
    df["discount_percentage"]
    .astype(str)
    .str.replace("%", "", regex=False)
)

df["discount_percentage"] = pd.to_numeric(
    df["discount_percentage"],
    errors="coerce"
)

# ==========================================
# Clean Rating
# ==========================================

df["rating"] = pd.to_numeric(
    df["rating"],
    errors="coerce"
)

# ==========================================
# Remove Missing Values
# ==========================================

df = df.dropna(
    subset=[
        "category",
        "discounted_price",
        "rating"
    ]
)

# ==========================================
# Category Summary
# ==========================================

category_summary = (

    df.groupby("category")

    .agg(

        Total_Products=("product_id", "count"),

        Average_Price=("discounted_price", "mean"),

        Average_Rating=("rating", "mean"),

        Average_Discount=("discount_percentage", "mean"),

        Lowest_Price=("discounted_price", "min"),

        Highest_Price=("discounted_price", "max")

    )

    .round(2)

    .sort_values(
        by="Total_Products",
        ascending=False
    )

)

print("\nCATEGORY SUMMARY\n")

print(category_summary)

# ==========================================
# Save Report
# ==========================================

category_summary.to_csv(
    "reports/category_summary.csv"
)

print("\nReport Saved Successfully!")