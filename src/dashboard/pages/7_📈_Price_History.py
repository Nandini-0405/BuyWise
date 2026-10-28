"""
BuyWise - Price History Page
Shows real price history from the price_history table.
Falls back to simulated data if the table is empty (early stage).
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
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

from config import DB_PATH

st.set_page_config(page_title="Price History | BuyWise", page_icon="📈", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">📈 Price History</div>', unsafe_allow_html=True)
st.write("See how a product's price has changed over time to determine if now is the right time to buy.")

# ── Product Search ────────────────────────────────────────────────
st.markdown("### Search Product")
search_term = st.text_input("Enter product name or brand...", placeholder="e.g. Headphones")

filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df["product_name"].str.contains(search_term, case=False, na=False)]

if len(filtered_df) == 0:
    st.warning("No products found.")
    st.stop()

selected_product = st.selectbox("Select a Product to view its Price History", filtered_df["product_name"].head(100).tolist())
product_data = df[df["product_name"] == selected_product].iloc[0]
asin = str(product_data.get("product_id", ""))

# ── Load Real Price History ───────────────────────────────────────
history_df = pd.DataFrame()

try:
    conn = sqlite3.connect(DB_PATH)
    history_df = pd.read_sql(
        "SELECT scraped_at, price, actual_price, discount_pct FROM price_history "
        "WHERE product_id = ? ORDER BY scraped_at ASC",
        conn, params=(asin,)
    )
    conn.close()
except Exception:
    pass

using_real_data = len(history_df) > 1

if not using_real_data:
    # ── Simulated fallback ────────────────────────────────────────
    st.info("💡 Real price history will appear here after a few days of tracking. Showing simulated data for now.")
    current_price = product_data["discounted_price"]
    actual_price  = product_data["actual_price"]
    if pd.isna(current_price) or current_price == 0:
        st.error("Price data not available for this product.")
        st.stop()
    if pd.isna(actual_price) or actual_price <= current_price:
        actual_price = current_price * 1.5

    seed = sum(ord(c) for c in asin)
    np.random.seed(seed)

    today = datetime.now()
    dates = [today - timedelta(days=30 * i) for i in range(5, -1, -1)]
    prices = [actual_price] + list(np.random.uniform(current_price, actual_price, 4)) + [current_price]

    history_df = pd.DataFrame({
        "scraped_at":   [d.strftime("%Y-%m-%d") for d in dates],
        "price":        [round(p, 0) for p in prices],
        "actual_price": [round(actual_price, 0)] * 6,
        "discount_pct": [round((actual_price - p) / actual_price * 100, 1) for p in prices],
    })
else:
    st.success(f"✅ Showing {len(history_df)} days of real tracked price data.")

# ── KPIs ──────────────────────────────────────────────────────────
current_p  = history_df["price"].iloc[-1]
highest_p  = history_df["price"].max()
lowest_p   = history_df["price"].min()
avg_p      = history_df["price"].mean()
volatility = history_df["price"].std() / avg_p * 100 if avg_p > 0 else 0
price_drops = (history_df["price"].diff() < 0).sum()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.markdown(f'<div class="metric-card"><div class="metric-label">Current Price</div><div class="metric-value">₹{current_p:,.0f}</div></div>', unsafe_allow_html=True)
kpi2.markdown(f'<div class="metric-card"><div class="metric-label">All-Time Low</div><div class="metric-value">₹{lowest_p:,.0f}</div></div>', unsafe_allow_html=True)
kpi3.markdown(f'<div class="metric-card"><div class="metric-label">All-Time High</div><div class="metric-value">₹{highest_p:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

kpi4, kpi5, kpi6 = st.columns(3)
kpi4.markdown(f'<div class="metric-card"><div class="metric-label">Average Price</div><div class="metric-value">₹{avg_p:,.0f}</div></div>', unsafe_allow_html=True)
kpi5.markdown(f'<div class="metric-card"><div class="metric-label">Price Volatility</div><div class="metric-value">{volatility:.1f}%</div></div>', unsafe_allow_html=True)
kpi6.markdown(f'<div class="metric-card"><div class="metric-label">Price Drops Tracked</div><div class="metric-value">{price_drops}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Plotly Chart ──────────────────────────────────────────────────
st.markdown("### Price Trend")

fig = go.Figure()

# MRP line (dashed)
if "actual_price" in history_df.columns:
    fig.add_trace(go.Scatter(
        x=history_df["scraped_at"], y=history_df["actual_price"],
        mode="lines", name="MRP", line=dict(color="#e5e7eb", dash="dash", width=1.5),
    ))

# Price area
fig.add_trace(go.Scatter(
    x=history_df["scraped_at"], y=history_df["price"],
    mode="lines+markers", name="Selling Price",
    line=dict(color="#6366f1", width=3),
    marker=dict(size=7, color="#6366f1"),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
))

# Lowest price annotation
min_idx = history_df["price"].idxmin()
fig.add_annotation(
    x=history_df.loc[min_idx, "scraped_at"],
    y=history_df.loc[min_idx, "price"],
    text=f"🔽 Lowest ₹{history_df.loc[min_idx, 'price']:,.0f}",
    showarrow=True, arrowhead=2, arrowcolor="#10b981",
    font=dict(color="#10b981", size=12),
)

fig.update_layout(
    xaxis_title="Date", yaxis_title="Price (₹)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="white", paper_bgcolor="white",
    height=420,
    margin=dict(l=40, r=40, t=40, b=40),
)
fig.update_yaxes(tickprefix="₹", gridcolor="#f3f4f6")
fig.update_xaxes(gridcolor="#f3f4f6")

st.plotly_chart(fig, use_container_width=True)

# ── Data Table ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Historical Data")
display = history_df.copy()
display["price"]        = display["price"].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
display["actual_price"] = display["actual_price"].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
display["discount_pct"] = display["discount_pct"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
display = display.rename(columns={
    "scraped_at": "Date", "price": "Selling Price",
    "actual_price": "MRP", "discount_pct": "Discount"
})
st.dataframe(display, use_container_width=True, hide_index=True)
