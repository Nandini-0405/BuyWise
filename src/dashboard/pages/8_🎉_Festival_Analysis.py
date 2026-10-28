"""
BuyWise - Festival Analysis Page
Compares prices during Indian sale seasons using real price_history data.
"""

import sys
from pathlib import Path

# Ensure dashboard and root directories are in sys.path
_P = Path(__file__).resolve()
for _dir in [_P.parents[1], _P.parents[2], _P.parents[3]]:
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

from config import DB_PATH

st.set_page_config(page_title="Festival Analysis | BuyWise", page_icon="🎉", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🎉 Festival & Sale Season Analysis</div>', unsafe_allow_html=True)
st.write("Discover which Indian sale events offer the deepest discounts and the best time to buy.")

# ── Indian Sale Events Calendar ───────────────────────────────────
SALE_SEASONS = {
    "Republic Day Sale":       ("01-20", "01-26"),
    "Holi Sale":               ("03-20", "03-31"),
    "Prime Day":               ("07-16", "07-18"),
    "Independence Day Sale":   ("08-10", "08-15"),
    "Great Indian Festival":   ("10-01", "10-15"),
    "Diwali Sale":             ("10-25", "11-05"),
    "Black Friday":            ("11-27", "11-30"),
    "Year-End Sale":           ("12-26", "12-31"),
}

# ── Check if we have real history data ────────────────────────────
history_df = pd.DataFrame()
try:
    conn = sqlite3.connect(DB_PATH)
    history_df = pd.read_sql(
        "SELECT ph.product_id, ph.scraped_at, ph.price, ph.discount_pct, p.category_clean "
        "FROM price_history ph "
        "JOIN products p ON ph.product_id = p.product_id "
        "ORDER BY ph.scraped_at",
        conn
    )
    conn.close()
    history_df["scraped_at"] = pd.to_datetime(history_df["scraped_at"])
except Exception:
    pass

has_real_data = len(history_df) > 0

# ── Sale Events Info Cards ────────────────────────────────────────
st.markdown("### 📅 Indian Sale Events Calendar")

months_map = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
}

sale_cols = st.columns(4)
for i, (sale_name, (start, end)) in enumerate(SALE_SEASONS.items()):
    month = months_map.get(start[:2], start[:2])
    with sale_cols[i % 4]:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center; padding:1rem;">
            <div style="font-size:1.5rem;">🛒</div>
            <div style="font-weight:700; color:#6366f1; font-size:0.85rem; margin:0.3rem 0;">{sale_name}</div>
            <div style="color:#6b7280; font-size:0.78rem;">{month} {start[3:]} – {end[3:]}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Historical Analysis or Snapshot Analysis ─────────────────────
if has_real_data:
    st.markdown("### 📊 Price Drops During Sale Events (Real Data)")

    def get_season(dt):
        mm_dd = dt.strftime("%m-%d")
        for name, (start, end) in SALE_SEASONS.items():
            if start <= mm_dd <= end:
                return name
        return "Regular Day"

    history_df["season"] = history_df["scraped_at"].apply(get_season)
    season_stats = (
        history_df.groupby("season")
        .agg(
            Avg_Price=("price", "mean"),
            Avg_Discount=("discount_pct", "mean"),
            Data_Points=("price", "count"),
        )
        .reset_index()
        .sort_values("Avg_Discount", ascending=False)
    )

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            season_stats, x="season", y="Avg_Discount",
            title="Average Discount by Season",
            color="Avg_Discount", color_continuous_scale="Purples",
            labels={"season": "Sale Event", "Avg_Discount": "Avg Discount (%)"},
        )
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            season_stats, x="season", y="Avg_Price",
            title="Average Selling Price by Season",
            color="Avg_Price", color_continuous_scale="Blues_r",
            labels={"season": "Sale Event", "Avg_Price": "Avg Price (₹)"},
        )
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(season_stats.rename(columns={
        "season": "Event", "Avg_Price": "Avg Price (₹)",
        "Avg_Discount": "Avg Discount (%)", "Data_Points": "Data Points"
    }), use_container_width=True, hide_index=True)

else:
    # ── Snapshot-based analysis (current data) ────────────────────
    st.info("📊 Real sale-season price tracking will appear once the daily pipeline has run during a sale event. Below is an analysis based on current discount data.")

    cat_discount = (
        df.groupby("category_clean")["discount_percentage"]
        .agg(["mean", "max", "count"])
        .reset_index()
        .rename(columns={"mean": "Avg Discount", "max": "Max Discount", "count": "Products", "category_clean": "Category"})
        .sort_values("Avg Discount", ascending=False)
        .head(12)
    )

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            cat_discount, x="Category", y="Avg Discount",
            title="Average Discount by Category (Current Data)",
            color="Avg Discount", color_continuous_scale="Purples",
        )
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            cat_discount, x="Category", y="Max Discount",
            title="Maximum Discount by Category",
            color="Max Discount", color_continuous_scale="Reds",
        )
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    # Big discounts table
    st.markdown("### 🔥 Products with 60%+ Discounts Right Now")
    big_deals = df[df["discount_percentage"] >= 60][
        ["product_name", "brand", "category_clean", "discounted_price", "actual_price", "discount_percentage", "rating"]
    ].sort_values("discount_percentage", ascending=False).head(20)

    if len(big_deals) > 0:
        big_deals["discounted_price"] = big_deals["discounted_price"].apply(lambda x: f"₹{x:,.0f}")
        big_deals["actual_price"]     = big_deals["actual_price"].apply(lambda x: f"₹{x:,.0f}")
        big_deals["discount_percentage"] = big_deals["discount_percentage"].apply(lambda x: f"{x:.0f}%")
        big_deals = big_deals.rename(columns={
            "product_name": "Product", "brand": "Brand",
            "category_clean": "Category", "discounted_price": "Price",
            "actual_price": "MRP", "discount_percentage": "Discount", "rating": "Rating"
        })
        st.dataframe(big_deals, use_container_width=True, hide_index=True)
    else:
        st.write("No products with 60%+ discount found in the current dataset.")
