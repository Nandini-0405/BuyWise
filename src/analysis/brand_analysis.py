"""
BuyWise
Brand Intelligence Engine
"""

import sqlite3
import pandas as pd

DATABASE = "database/buywise.db"

conn = sqlite3.connect(DATABASE)

query = """
SELECT
product_name,
category,
discounted_price,
actual_price,
discount_percentage,
rating
FROM products;
"""

df = pd.read_sql(query, conn)

conn.close()

# ------------------------------------------
# Cleaning
# ------------------------------------------

df["discounted_price"] = (
    df["discounted_price"]
    .astype(str)
    .str.replace("₹","",regex=False)
    .str.replace(",","",regex=False)
)

df["discounted_price"] = pd.to_numeric(
    df["discounted_price"],
    errors="coerce"
)

df["discount_percentage"] = (
    df["discount_percentage"]
    .astype(str)
    .str.replace("%","",regex=False)
)

df["discount_percentage"] = pd.to_numeric(
    df["discount_percentage"],
    errors="coerce"
)

# ------------------------------------------
# Extract Brand
# ------------------------------------------

brands = [
    "Apple",
    "Samsung",
    "Boat",
    "Sony",
    "HP",
    "Dell",
    "LG",
    "Lenovo",
    "OnePlus",
    "JBL",
    "Noise",
    "Philips",
    "Canon",
    "Nikon",
    "Mi",
    "Redmi",
    "Realme",
    "Asus",
    "Acer"
]


def extract_brand(name):

    for brand in brands:

        if brand.lower() in str(name).lower():

            return brand

    return "Other"


df["brand"] = df["product_name"].apply(extract_brand)

# ------------------------------------------
# Brand Summary
# ------------------------------------------

summary = (

    df.groupby("brand")

    .agg(

        Products=("brand","count"),

        Avg_Price=("discounted_price","mean"),

        Avg_Rating=("rating","mean"),

        Avg_Discount=("discount_percentage","mean")

    )

    .sort_values(

        by="Products",

        ascending=False

    )

)

print(summary)
summary.to_csv(
    "reports/brand_summary.csv"
)

print("\nBrand report saved.")