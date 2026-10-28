"""
BuyWise - Price Prediction Page
Uses Linear Regression on price_history to predict future prices.
Falls back to trend estimation when history is limited.
"""

import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
from utils import apply_custom_css, load_data

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import DB_PATH

st.set_page_config(page_title="Price Prediction | BuyWise", page_icon="🤖", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🤖 Price Prediction</div>', unsafe_allow_html=True)
st.write("AI-powered price forecast — know where a product's price is heading before you buy.")

# ── Product Search ─────────────────────────────────────────────────
search_term = st.text_input("Search for a product...", placeholder="e.g. Laptop, Samsung, boAt")
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

if pd.isna(current_price) or current_price == 0:
    st.error("Price data unavailable.")
    st.stop()

# ── Prediction horizon ────────────────────────────────────────────
horizon_days = st.slider("Predict prices for next N days:", min_value=7, max_value=60, value=30, step=7)

# ── Load History ──────────────────────────────────────────────────
history_df = pd.DataFrame()
try:
    conn = sqlite3.connect(DB_PATH)
    history_df = pd.read_sql(
        "SELECT scraped_at, price FROM price_history WHERE product_id=? ORDER BY scraped_at ASC",
        conn, params=(asin,)
    )
    conn.close()
    history_df["scraped_at"] = pd.to_datetime(history_df["scraped_at"])
except Exception:
    pass

has_real = len(history_df) >= 7

if has_real:
    st.success(f"✅ Training on {len(history_df)} days of real price history.")
    hist_prices = history_df["price"].values
    hist_dates  = history_df["scraped_at"].tolist()
else:
    st.info("💡 Real price history is being collected. Predictions below are estimated from the product's MRP and current price pattern.")
    actual_price = product_data["actual_price"]
    if pd.isna(actual_price) or actual_price <= current_price:
        actual_price = current_price * 1.4
    seed = sum(ord(c) for c in asin)
    np.random.seed(seed)
    n_sim = 30
    today = date.today()
    hist_dates  = [pd.Timestamp(today - timedelta(days=n_sim - i)) for i in range(n_sim)]
    hist_prices = np.linspace(actual_price, current_price, n_sim) + np.random.normal(0, current_price * 0.03, n_sim)
    history_df = pd.DataFrame({"scraped_at": hist_dates, "price": hist_prices})

# ── Linear Regression ─────────────────────────────────────────────
from sklearn.linear_model import LinearRegression

X = np.arange(len(hist_prices)).reshape(-1, 1)
y = np.array(hist_prices)
model = LinearRegression().fit(X, y)

# Future dates
future_x = np.arange(len(hist_prices), len(hist_prices) + horizon_days).reshape(-1, 1)
future_prices = model.predict(future_x)

# Clip to realistic range
lower_bound = current_price * 0.50
upper_bound = current_price * 1.50
future_prices = np.clip(future_prices, lower_bound, upper_bound)

last_date = history_df["scraped_at"].iloc[-1]
future_dates = [last_date + timedelta(days=i + 1) for i in range(horizon_days)]

# ── Prediction Summary ────────────────────────────────────────────
predicted_end = future_prices[-1]
direction = "📉 Dropping" if predicted_end < current_price else "📈 Rising" if predicted_end > current_price * 1.02 else "➡️ Stable"
change_pct = (predicted_end - current_price) / current_price * 100

c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="metric-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-value">₹{current_price:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card"><div class="metric-label">PREDICTED IN {horizon_days}D</div><div class="metric-value">₹{predicted_end:,.0f}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card"><div class="metric-label">TREND</div><div class="metric-value">{direction} ({change_pct:+.1f}%)</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if change_pct < -3:
    st.warning(f"⏳ Price is predicted to drop by {abs(change_pct):.1f}% — consider **waiting** before buying.")
elif change_pct > 3:
    st.error(f"⚡ Price is predicted to rise by {change_pct:.1f}% — consider **buying now** before it goes up.")
else:
    st.success("✅ Price is predicted to remain relatively stable. Buy when it suits you.")

# ── Chart ─────────────────────────────────────────────────────────
st.markdown("### Price Forecast Chart")
fig = go.Figure()

# History
fig.add_trace(go.Scatter(
    x=history_df["scraped_at"], y=history_df["price"],
    mode="lines+markers", name="Historical Price",
    line=dict(color="#6366f1", width=2.5),
    marker=dict(size=5),
))

# Prediction band (±5% confidence)
upper_band = future_prices * 1.05
lower_band = future_prices * 0.95

fig.add_trace(go.Scatter(
    x=future_dates + future_dates[::-1],
    y=list(upper_band) + list(lower_band[::-1]),
    fill="toself", fillcolor="rgba(249,115,22,0.1)",
    line=dict(color="rgba(0,0,0,0)"), name="Confidence Band",
    showlegend=True,
))

fig.add_trace(go.Scatter(
    x=future_dates, y=future_prices,
    mode="lines", name="Predicted Price",
    line=dict(color="#f97316", width=2.5, dash="dash"),
))

# Vertical separator
fig.add_vline(x=str(history_df["scraped_at"].iloc[-1].date()),
              line_dash="dot", line_color="#9ca3af",
              annotation_text="Today", annotation_position="top")

fig.update_layout(
    height=420, plot_bgcolor="white", paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40),
)
fig.update_yaxes(tickprefix="₹", gridcolor="#f3f4f6")
fig.update_xaxes(gridcolor="#f3f4f6")
st.plotly_chart(fig, use_container_width=True)

st.caption("⚠️ Predictions use linear regression on available price history. Actual prices depend on Amazon's pricing, promotions, and demand. This is not financial advice.")
