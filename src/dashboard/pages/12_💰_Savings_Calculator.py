"""
BuyWise - Savings Calculator Page
Calculate exactly how much you save, and whether waiting is worth it.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import apply_custom_css, load_data

st.set_page_config(page_title="Savings Calculator | BuyWise", page_icon="💰", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">💰 Savings Calculator</div>', unsafe_allow_html=True)
st.write("Calculate exactly how much you save and whether it's worth waiting for a better deal.")

# ── Mode Toggle ────────────────────────────────────────────────────
mode = st.radio("What do you want to calculate?", [
    "🛒 How much I save on a product",
    "⏳ Is waiting for a sale worth it?",
    "💸 EMI vs Lump Sum",
], horizontal=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# MODE 1 — Product Savings
# ═══════════════════════════════════════════════════════════════════
if "How much I save" in mode:
    st.markdown("### 🛒 Product Savings Breakdown")

    search = st.text_input("Search a product", placeholder="e.g. OnePlus, boAt, Sony")
    results = df.copy()
    if search:
        results = results[results["product_name"].str.contains(search, case=False, na=False)]

    if len(results) == 0:
        st.warning("No products match your search.")
        st.stop()

    options = {}
    for i, r in results.head(50).iterrows():
        p_name = str(r['product_name'])[:60]
        p_price = float(r['discounted_price']) if pd.notnull(r['discounted_price']) else 0.0
        options[f"{p_name} (₹{p_price:,.0f})"] = i

    chosen_label = st.selectbox("Select product", list(options.keys()))
    chosen_idx = options[chosen_label]
    row = df.loc[chosen_idx]

    qty = st.number_input("Quantity to buy", min_value=1, max_value=20, value=1)

    mrp = float(row.get("actual_price", 0) or 0) * qty
    sale_price = float(row.get("discounted_price", 0) or 0) * qty
    saved = max(0.0, mrp - sale_price)
    saved_pct = float(row.get("discount_percentage", 0) or 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">MRP (Total)</div><div class="metric-value">₹{mrp:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">You Pay</div><div class="metric-value">₹{sale_price:,.0f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border:2px solid #10b981;"><div class="metric-label">You Save</div><div class="metric-value" style="color:#10b981;">₹{saved:,.0f}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Discount</div><div class="metric-value">{saved_pct:.0f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visual bar
    fig = go.Figure(go.Bar(
        x=["MRP", "Sale Price", "Savings"],
        y=[mrp, sale_price, saved],
        marker_color=["#e5e7eb", "#6366f1", "#10b981"],
        text=[f"₹{mrp:,.0f}", f"₹{sale_price:,.0f}", f"₹{saved:,.0f}"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Price Breakdown",
        yaxis_title="Amount (₹)", plot_bgcolor="white", paper_bgcolor="white",
        height=350, margin=dict(t=50, b=20),
    )
    fig.update_yaxes(tickprefix="₹", gridcolor="#f3f4f6")
    st.plotly_chart(fig, use_container_width=True)

    if saved_pct >= 50:
        st.success(f"🔥 Excellent deal! You're saving over half the MRP.")
    elif saved_pct >= 30:
        st.success(f"✅ Good deal! Saving {saved_pct:.0f}% is solid value.")
    elif saved_pct >= 10:
        st.info(f"🟡 Moderate discount. Worth buying if you need it now.")
    else:
        st.warning(f"🔴 Low discount. Consider waiting for a better deal.")

# ═══════════════════════════════════════════════════════════════════
# MODE 2 — Is Waiting Worth It?
# ═══════════════════════════════════════════════════════════════════
elif "worth it" in mode:
    st.markdown("### ⏳ Is Waiting for a Sale Worth It?")
    st.write("Enter the product price now and your expected sale price. We'll calculate if waiting makes financial sense.")

    col_a, col_b = st.columns(2)
    current_p  = col_a.number_input("Current Price (₹)", min_value=100.0, value=15000.0, step=500.0)
    expected_p = col_b.number_input("Expected Sale Price (₹)", min_value=100.0, value=12000.0, step=500.0)

    col_c, col_d = st.columns(2)
    wait_days = col_c.slider("How many days will you wait?", 1, 90, 30)
    daily_need = col_d.selectbox("How urgently do you need it?", ["Not urgent", "Somewhat urgent", "Very urgent"])

    savings    = current_p - expected_p
    savings_pct = savings / current_p * 100 if current_p > 0 else 0
    per_day_saving = savings / wait_days if wait_days > 0 else 0

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">EXPECTED SAVINGS</div><div class="metric-value" style="color:#10b981;">₹{savings:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">SAVINGS %</div><div class="metric-value">{savings_pct:.1f}%</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">SAVINGS PER DAY WAITED</div><div class="metric-value">₹{per_day_saving:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Decision logic
    urgency_factor = {"Not urgent": 1.0, "Somewhat urgent": 0.6, "Very urgent": 0.2}[daily_need]
    adjusted_score = savings_pct * urgency_factor

    if adjusted_score >= 20:
        st.success(f"✅ **WAIT** — The saving of ₹{savings:,.0f} ({savings_pct:.1f}%) is worth waiting {wait_days} days.")
    elif adjusted_score >= 8:
        st.info(f"🟡 **MAYBE WAIT** — Savings are decent but depends on how much you need it now.")
    else:
        st.warning(f"🔴 **BUY NOW** — The expected saving is small or you need it urgently. Not worth the wait.")

# ═══════════════════════════════════════════════════════════════════
# MODE 3 — EMI Calculator
# ═══════════════════════════════════════════════════════════════════
else:
    st.markdown("### 💸 EMI vs Lump Sum Calculator")

    col1, col2, col3 = st.columns(3)
    price         = col1.number_input("Product Price (₹)", min_value=1000.0, value=50000.0, step=1000.0)
    interest_rate = col2.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=36.0, value=15.0, step=0.5)
    tenure_months = col3.slider("EMI Tenure (months)", 3, 36, 12, step=3)

    monthly_rate = interest_rate / 100 / 12

    if monthly_rate > 0:
        emi = price * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
    else:
        emi = price / tenure_months

    total_payment = emi * tenure_months
    total_interest = total_payment - price

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Monthly EMI</div><div class="metric-value">₹{emi:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Total Payment</div><div class="metric-value">₹{total_payment:,.0f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border:2px solid #ef4444;"><div class="metric-label">Interest Paid</div><div class="metric-value" style="color:#ef4444;">₹{total_interest:,.0f}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Effective Extra Cost</div><div class="metric-value">{total_interest/price*100:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure(go.Pie(
        labels=["Product Price", "Interest"],
        values=[price, total_interest],
        hole=0.5,
        marker_colors=["#6366f1", "#ef4444"],
    ))
    fig.update_layout(title="What You Actually Pay", height=300, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    if total_interest > 0:
        st.info(f"💡 **Tip:** Paying ₹{price:,.0f} upfront saves you ₹{total_interest:,.0f} in interest ({total_interest/price*100:.1f}% extra cost). If you have the funds, lump sum is always better.")
