import sqlite3
import pandas as pd

conn = sqlite3.connect("database/buywise.db")

df = pd.read_sql("SELECT * FROM products", conn)

conn.close()

# -------------------------

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

# -------------------------

conditions = (

    (df["rating"] >= 4.3)

    &

    (df["discount_percentage"] >= 35)

)

df["recommendation"] = "Not Recommended"

df.loc[conditions, "recommendation"] = "Highly Recommended"

recommended = df[

    df["recommendation"] == "Highly Recommended"

]

recommended.to_csv(

    "reports/recommended_products.csv",

    index=False

)

print(

recommended[
[
"product_name",
"rating",
"discount_percentage"
]
]

)
