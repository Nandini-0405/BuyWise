import streamlit as st
import plotly.express as px
import pandas as pd
from utils import apply_custom_css, load_data

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="BuyWise | Home",
    page_icon="🏠",
    layout="wide",
)

# Apply shared styling
apply_custom_css()

# Load data
df = load_data()

# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown("""
<div class="bw-header">
    <h1>🏠 Home</h1>
    <p>What's happening in the marketplace?</p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# KPI row
# --------------------------------------------------

total_products   = len(df)
total_categories = df["category_clean"].nunique()
avg_price        = round(df["discounted_price"].mean(), 0)
avg_discount     = round(df["discount_percentage"].mean(), 1)
avg_rating       = round(df["rating"].mean(), 2)

col1, col2, col3, col4, col5 = st.columns(5)

kpis = [
    (col1, "Products",       f"{total_products:,}",      "in catalogue"),
    (col2, "Categories",     f"{total_categories}",       "unique"),
    (col3, "Avg Price",      f"₹{avg_price:,.0f}",        "discounted"),
    (col4, "Avg Discount",   f"{avg_discount}%",          "off MRP"),
    (col5, "Avg Rating",     f"{avg_rating} ★",           "out of 5"),
]

for col, label, value, sub in kpis:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------
# Charts
# --------------------------------------------------

st.markdown('<div class="section-title">Marketplace Overview</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Products by category
    cat_counts = df["category_clean"].value_counts().reset_index().head(10)
    cat_counts.columns = ["Category", "Count"]
    fig1 = px.bar(cat_counts, x="Count", y="Category", orientation='h', title="Top Categories by Product Count", color_discrete_sequence=["#6366f1"])
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)
    
    # Top brands
    brand_counts = df["brand"].value_counts().reset_index().head(10)
    brand_counts.columns = ["Brand", "Count"]
    fig3 = px.bar(brand_counts, x="Brand", y="Count", title="Top Brands by Product Count", color_discrete_sequence=["#f59e0b"])
    st.plotly_chart(fig3, use_container_width=True)

with chart_col2:
    # Average discount by category
    cat_discount = df.groupby("category_clean")["discount_percentage"].mean().reset_index().sort_values("discount_percentage", ascending=False).head(10)
    fig2 = px.bar(cat_discount, x="category_clean", y="discount_percentage", title="Average Discount by Category (%)", color_discrete_sequence=["#10b981"])
    st.plotly_chart(fig2, use_container_width=True)

    # Price distribution
    fig4 = px.histogram(df[df["discounted_price"] <= df["discounted_price"].quantile(0.95)], x="discounted_price", nbins=40, title="Price Distribution (Discounted Price)", color_discrete_sequence=["#8b5cf6"])
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------
# Highlights
# --------------------------------------------------

st.markdown('<div class="section-title">Highlights</div>', unsafe_allow_html=True)

# Calculate Highlights
# Best deal: High discount and high rating
best_deal_df = df[(df["discount_percentage"] > 50) & (df["rating"] >= 4.0)]
best_deal = best_deal_df.sort_values("discount_amount", ascending=False).iloc[0] if not best_deal_df.empty else df.iloc[0]

# Highest-rated product
highest_rated = df[df["rating_count"] > 500].sort_values("rating", ascending=False).iloc[0]

# Biggest discount
biggest_discount = df.sort_values("discount_percentage", ascending=False).iloc[0]

# Most expensive product
most_expensive = df.sort_values("actual_price", ascending=False).iloc[0]

# Best-value product: high rating, high rating count, low price
best_value_df = df[(df["rating"] >= 4.2) & (df["rating_count"] > 1000)]
best_value = best_value_df.sort_values("discounted_price", ascending=True).iloc[0] if not best_value_df.empty else df.iloc[0]

hl_col1, hl_col2, hl_col3, hl_col4, hl_col5 = st.columns(5)

highlights = [
    (hl_col1, "🔥 Best Deal", best_deal["product_name"][:40] + "...", f"₹{best_deal['discounted_price']:,.0f} ({best_deal['discount_percentage']}% off)"),
    (hl_col2, "⭐ Highest-Rated", highest_rated["product_name"][:40] + "...", f"{highest_rated['rating']} ★ ({highest_rated['rating_count']:,.0f} reviews)"),
    (hl_col3, "💰 Biggest Discount", biggest_discount["product_name"][:40] + "...", f"{biggest_discount['discount_percentage']}% off (Saved ₹{biggest_discount['discount_amount']:,.0f})"),
    (hl_col4, "💎 Most Expensive", most_expensive["product_name"][:40] + "...", f"MRP: ₹{most_expensive['actual_price']:,.0f}"),
    (hl_col5, "🏷 Best-Value", best_value["product_name"][:40] + "...", f"₹{best_value['discounted_price']:,.0f} with {best_value['rating']} ★"),
]

for col, title, name, stat in highlights:
    with col:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; height: 100%;">
            <div style="font-size: 0.85rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">{title}</div>
            <div style="font-size: 0.9rem; font-weight: 500; color: #111827; margin-bottom: 0.25rem;">{name}</div>
            <div style="font-size: 0.8rem; color: #6b7280;">{stat}</div>
        </div>
        """, unsafe_allow_html=True)