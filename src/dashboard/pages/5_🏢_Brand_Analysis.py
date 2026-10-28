import sys
from pathlib import Path

# Ensure dashboard and root directories are in sys.path
_P = Path(__file__).resolve()
for _dir in [_P.parents[1], _P.parents[2], _P.parents[3]]:
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import streamlit as st
import pandas as pd
try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

st.set_page_config(page_title="Brand Analysis | BuyWise", page_icon="🏢", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🏢 Brand Analysis</div>', unsafe_allow_html=True)
st.write("Compare brands based on price, ratings and discounts.")

# Brand stats
brand_stats = df.groupby("brand").agg(
    Products=("product_name", "count"),
    Avg_Price=("discounted_price", "mean"),
    Avg_Rating=("rating", "mean"),
    Avg_Discount=("discount_percentage", "mean")
).reset_index()

# Filter out brands with too few products to avoid noisy metrics
brand_stats = brand_stats[brand_stats["Products"] >= 3]

# Layout for Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 10 Brands by Products")
    top_products = brand_stats.sort_values("Products", ascending=False).head(10).set_index("brand")
    st.bar_chart(top_products["Products"])

with col2:
    st.markdown("### Average Price by Brand (Top 10)")
    top_price = brand_stats.sort_values("Avg_Price", ascending=False).head(10).set_index("brand")
    st.bar_chart(top_price["Avg_Price"])

col3, col4 = st.columns(2)

with col3:
    st.markdown("### Average Rating by Brand (Top 10)")
    top_rating = brand_stats.sort_values("Avg_Rating", ascending=False).head(10).set_index("brand")
    st.bar_chart(top_rating["Avg_Rating"])

with col4:
    st.markdown("### Average Discount by Brand (Top 10)")
    top_discount = brand_stats.sort_values("Avg_Discount", ascending=False).head(10).set_index("brand")
    st.bar_chart(top_discount["Avg_Discount"])

st.markdown("### Brand Price vs Rating")
# Use a scatter chart to see if more expensive brands get better ratings
st.scatter_chart(brand_stats, x="Avg_Price", y="Avg_Rating", color="brand")

st.markdown("---")
st.markdown("### Brand Performance Overview")

display_df = brand_stats.sort_values("Products", ascending=False).copy()
display_df["Avg_Price"] = display_df["Avg_Price"].apply(lambda x: f"₹{x:,.0f}")
display_df["Avg_Rating"] = display_df["Avg_Rating"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
display_df["Avg_Discount"] = display_df["Avg_Discount"].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")

display_df = display_df.rename(columns={
    "brand": "Brand",
    "Products": "Products",
    "Avg_Price": "Avg Price",
    "Avg_Rating": "Avg Rating",
    "Avg_Discount": "Avg Discount"
})

st.dataframe(display_df, use_container_width=True, hide_index=True)

