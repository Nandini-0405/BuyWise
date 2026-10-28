import streamlit as st
import pandas as pd
from utils import apply_custom_css, load_data

st.set_page_config(page_title="Discount Intelligence | BuyWise", page_icon="💰", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">💰 Discount Intelligence</div>', unsafe_allow_html=True)

# KPIs
avg_discount = df["discount_percentage"].mean()
max_discount = df["discount_percentage"].max()
products_on_discount = len(df[df["discount_percentage"] > 0])
avg_selling_price = df["discounted_price"].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.markdown(f'<div class="metric-card"><div class="metric-label">Average Discount</div><div class="metric-value">{avg_discount:.1f}%</div></div>', unsafe_allow_html=True)
kpi2.markdown(f'<div class="metric-card"><div class="metric-label">Maximum Discount</div><div class="metric-value">{max_discount:.0f}%</div></div>', unsafe_allow_html=True)
kpi3.markdown(f'<div class="metric-card"><div class="metric-label">Products on Discount</div><div class="metric-value">{products_on_discount:,}</div></div>', unsafe_allow_html=True)
kpi4.markdown(f'<div class="metric-card"><div class="metric-label">Avg. Selling Price</div><div class="metric-value">₹{avg_selling_price:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Layout for Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 10 Discounted Products")
    top_discounts = df.nlargest(10, "discount_percentage")[["product_name", "discount_percentage"]].copy()
    top_discounts["product_name"] = top_discounts["product_name"].apply(lambda x: x[:30] + "..." if isinstance(x, str) and len(x) > 30 else x)
    top_discounts_chart = top_discounts.set_index("product_name")
    st.bar_chart(top_discounts_chart)

with col2:
    st.markdown("### Average Discount by Category")
    avg_disc_cat = df.groupby("category_clean")["discount_percentage"].mean().sort_values(ascending=False).head(10)
    st.bar_chart(avg_disc_cat)

col3, col4 = st.columns(2)

with col3:
    st.markdown("### Average Discount by Brand")
    avg_disc_brand = df.groupby("brand")["discount_percentage"].mean().sort_values(ascending=False).head(10)
    st.bar_chart(avg_disc_brand)

with col4:
    st.markdown("### Discount Distribution")
    dist = df["discount_percentage"].dropna().value_counts(bins=10).sort_index()
    dist.index = [f"{int(i.left)}% - {int(i.right)}%" for i in dist.index]
    st.bar_chart(dist)

st.markdown("---")
st.markdown("### Top 10 Deepest Discounts")
top_discounts_table = df.sort_values(by="discount_percentage", ascending=False).head(10)

display_df = top_discounts_table[["product_name", "actual_price", "discounted_price", "discount_percentage"]].copy()

# Formatting
display_df["actual_price"] = display_df["actual_price"].apply(lambda x: f"₹{x:,.0f}")
display_df["discounted_price"] = display_df["discounted_price"].apply(lambda x: f"₹{x:,.0f}")
display_df["discount_percentage"] = display_df["discount_percentage"].apply(lambda x: f"{x:.0f}%")

display_df = display_df.rename(columns={
    "product_name": "Product",
    "actual_price": "MRP",
    "discounted_price": "Price",
    "discount_percentage": "Discount"
})

st.dataframe(display_df, use_container_width=True, hide_index=True)
