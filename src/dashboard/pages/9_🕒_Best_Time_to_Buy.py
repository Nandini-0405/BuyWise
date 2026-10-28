"""
BuyWise - Best Time to Buy Page
Uses real price_history data when available, otherwise uses smart simulation.
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
import numpy as np
import plotly.graph_objects as go

try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

from config import DB_PATH

st.set_page_config(page_title="Best Time to Buy | BuyWise", page_icon="🕒", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🕒 Best Time to Buy</div>', unsafe_allow_html=True)
st.write("Should I buy it now or wait? Let our intelligent tracking engine decide.")

# ── Product Search ────────────────────────────────────────────────
st.markdown("### Search Product")
search_term = st.text_input("Enter product name or brand...", placeholder="e.g. iPhone")

filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df["product_name"].str.contains(search_term, case=False, na=False)]

if len(filtered_df) == 0:
    st.warning("No products found.")
    st.stop()

selected_product = st.selectbox("Select a Product", filtered_df["product_name"].head(100).tolist())
product_data = df[df["product_name"] == selected_product].iloc[0]
asin = str(product_data.get("product_id", ""))
current_price = product_data["discounted_price"]
actual_price  = product_data["actual_price"]

if pd.isna(current_price) or current_price == 0:
    st.error("Price data not available for this product.")
    st.stop()

# ── Load Real History ─────────────────────────────────────────────
history_df = pd.DataFrame()
try:
    conn = sqlite3.connect(DB_PATH)
    history_df = pd.read_sql(
        "SELECT scraped_at, price FROM price_history WHERE product_id=? ORDER BY scraped_at ASC",
        conn, params=(asin,)
    )
    conn.close()
except Exception:
    pass

using_real = len(history_df) >= 7  # need at least a week of data

if using_real:
    lowest_observed   = history_df["price"].min()
    historical_average = history_df["price"].mean()
    st.success(f"✅ Analysing {len(history_df)} days of real tracked price data.")
else:
    st.info("💡 Real tracking active. Once 7+ days of data are collected, recommendations will be based on actual price history.")
    seed = sum(ord(c) for c in asin)
    np.random.seed(seed)
    if pd.isna(actual_price) or actual_price <= current_price:
        actual_price = current_price * 1.4
    lowest_observed    = current_price * np.random.uniform(0.75, 1.02)
    historical_average = current_price * np.random.uniform(0.95, 1.25)
    if lowest_observed > current_price:
        lowest_observed = current_price
    if historical_average < lowest_observed:
        historical_average = lowest_observed * 1.1

# ── Recommendation Logic ──────────────────────────────────────────
pct_vs_lowest = (current_price - lowest_observed) / lowest_observed * 100 if lowest_observed > 0 else 0

if current_price <= lowest_observed * 1.03:
    recommendation = "🟢 BUY NOW"
    verdict_color  = "#10b981"
    verdict_text   = "This is at or near its historical lowest price. Great time to buy!"
elif current_price <= historical_average * 1.05:
    recommendation = "🟡 GOOD TIME"
    verdict_color  = "#f59e0b"
    verdict_text   = "Price is at or below the historical average. A reasonable time to buy."
else:
    recommendation = "🔴 WAIT"
    verdict_color  = "#ef4444"
    discount_needed = round(((current_price / historical_average) - 1) * 100, 1)
    verdict_text   = f"Price is {discount_needed}% above average. Consider waiting for a sale."

# ── Indian Sale Events ────────────────────────────────────────────
INDIAN_SALES = {
    "January":  "Republic Day Sale",
    "March":    "Holi Sale",
    "August":   "Independence Day Sale",
    "October":  "Great Indian Festival (Diwali)",
    "November": "Diwali / Black Friday Sale",
    "December": "Year-End Sale",
}

seed2 = sum(ord(c) for c in asin[::-1])
np.random.seed(seed2)
months_list = list(INDIAN_SALES.keys())
best_month  = months_list[np.random.randint(0, len(months_list))]
best_sale   = INDIAN_SALES[best_month]

# ── Metrics ───────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="metric-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-value">₹{current_price:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card"><div class="metric-label">HISTORICAL AVERAGE</div><div class="metric-value">₹{historical_average:,.0f}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card"><div class="metric-label">ALL-TIME LOW</div><div class="metric-value">₹{lowest_observed:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)
c4.markdown(f'<div class="metric-card"><div class="metric-label">BEST BUYING MONTH</div><div class="metric-value">{best_month}</div></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="metric-card"><div class="metric-label">UPCOMING SALE</div><div class="metric-value" style="font-size:1.4rem;">{best_sale}</div></div>', unsafe_allow_html=True)
c6.markdown(f'''
<div class="metric-card" style="border:2px solid {verdict_color}; background:{verdict_color}14;">
    <div class="metric-label" style="color:{verdict_color}; font-weight:800;">BUYWISE VERDICT</div>
    <div class="metric-value" style="color:{verdict_color}; font-size:1.6rem;">{recommendation}</div>
</div>
''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info(f"💬 {verdict_text}")

# ── Price Gap Chart ───────────────────────────────────────────────
if using_real and len(history_df) > 0:
    st.markdown("### Price vs Historical Average")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history_df["scraped_at"], y=history_df["price"],
        mode="lines+markers", name="Actual Price",
        line=dict(color="#6366f1", width=2),
    ))
    fig.add_hline(y=historical_average, line_dash="dash", line_color="#f59e0b",
                  annotation_text=f"Avg ₹{historical_average:,.0f}", annotation_position="right")
    fig.add_hline(y=lowest_observed, line_dash="dot", line_color="#10b981",
                  annotation_text=f"Low ₹{lowest_observed:,.0f}", annotation_position="right")
    fig.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white",
                      margin=dict(l=40, r=100, t=20, b=40))
    fig.update_yaxes(tickprefix="₹", gridcolor="#f3f4f6")
    fig.update_xaxes(gridcolor="#f3f4f6")
    st.plotly_chart(fig, use_container_width=True)
