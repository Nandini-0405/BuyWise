"""
BuyWise
Discount Intelligence Engine
"""

import sqlite3
import pandas as pd

# -----------------------------------

DATABASE = "database/buywise.db"

conn = sqlite3.connect(DATABASE)

# -----------------------------------

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

# -----------------------------------
# Clean Discount %
# -----------------------------------

df["discount_percentage"] = (
    df["discount_percentage"]
    .astype(str)
    .str.replace("%","")
)

df["discount_percentage"] = pd.to_numeric(
    df["discount_percentage"],
    errors="coerce"
)

# -----------------------------------

highest_discount = (
    df.sort_values(
        by="discount_percentage",
        ascending=False
    )
)

print("="*80)
print("TOP 20 HIGHEST DISCOUNT PRODUCTS")
print("="*80)

print(
    highest_discount[
        [
            "product_name",
            "discount_percentage",
            "discounted_price",
            "actual_price"
        ]
    ].head(20)
)
print("\n")
print("="*80)
print("AVERAGE DISCOUNT BY CATEGORY")
print("="*80)

category_discount = (

    df.groupby("category")["discount_percentage"]

    .mean()

    .sort_values(ascending=False)

)

print(category_discount)
print("\n")
print("="*80)
print("BEST DEALS")
print("="*80)

best_deals = df[

    (df["rating"] >= 4.3)

    &

    (df["discount_percentage"] >= 40)

]

print(

best_deals[
[
"product_name",
"rating",
"discount_percentage"
]
].head(20)

)
df["discounted_price"] = pd.to_numeric(
    df["discounted_price"],
    errors="coerce"
)

print("\n")
print("="*80)
print("TOP 20 MOST EXPENSIVE PRODUCTS")
print("="*80)

print(

df.sort_values(

by="discounted_price",

ascending=False

)[

[
"product_name",
"discounted_price",
"rating"
]

].head(20)

)