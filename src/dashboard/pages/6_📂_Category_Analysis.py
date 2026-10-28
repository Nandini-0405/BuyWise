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

st.set_page_config(page_title="Category Analysis | BuyWise", page_icon="📂", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">📂 Category Analysis</div>', unsafe_allow_html=True)
st.write("Understand different product categories and discover where the best deals are hidden.")

# Calculate category statistics
cat_stats = df.groupby("category_clean").agg(
    Products=("product_name", "count"),
    Avg_Price=("discounted_price", "mean"),
    Avg_Rating=("rating", "mean"),
    Avg_Discount=("discount_percentage", "mean")
).reset_index()

# Layout for Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Products by Category")
    top_products = cat_stats.sort_values("Products", ascending=False).head(10).set_index("category_clean")
    st.bar_chart(top_products["Products"])

with col2:
    st.markdown("### Average Price by Category")
    top_price = cat_stats.sort_values("Avg_Price", ascending=False).head(10).set_index("category_clean")
    st.bar_chart(top_price["Avg_Price"])

col3, col4 = st.columns(2)

with col3:
    st.markdown("### Average Discount by Category")
    top_discount = cat_stats.sort_values("Avg_Discount", ascending=False).head(10).set_index("category_clean")
    st.bar_chart(top_discount["Avg_Discount"])

with col4:
    st.markdown("### Average Rating by Category")
    top_rating = cat_stats.sort_values("Avg_Rating", ascending=False).head(10).set_index("category_clean")
    st.bar_chart(top_rating["Avg_Rating"])

st.markdown("---")
st.markdown("### Category Performance Overview")

display_df = cat_stats.sort_values("Products", ascending=False).copy()
display_df["Avg_Price"] = display_df["Avg_Price"].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
display_df["Avg_Rating"] = display_df["Avg_Rating"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
display_df["Avg_Discount"] = display_df["Avg_Discount"].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")

display_df = display_df.rename(columns={
    "category_clean": "Category",
    "Products": "Products",
    "Avg_Price": "Avg Price",
    "Avg_Rating": "Avg Rating",
    "Avg_Discount": "Avg Discount"
})

st.dataframe(display_df, use_container_width=True, hide_index=True)
