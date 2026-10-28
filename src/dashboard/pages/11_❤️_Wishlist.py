"""
BuyWise - Wishlist Page
Save products to track with a personal target price.
Stored persistently in the buywise.db database.
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
from datetime import date

try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

from config import DB_PATH

st.set_page_config(page_title="Wishlist | BuyWise", page_icon="❤️", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">❤️ My Wishlist</div>', unsafe_allow_html=True)
st.write("Track your favourite products and get notified when the price hits your target.")

# ── DB helpers ─────────────────────────────────────────────────────

def get_wishlist() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        wl = pd.read_sql("""
            SELECT w.id, p.product_name, p.brand, p.category_clean,
                   p.discounted_price AS current_price, p.actual_price,
                   p.discount_percentage, p.rating, p.img_link, p.product_link,
                   w.target_price, w.added_at,
                   CASE WHEN p.discounted_price <= w.target_price THEN 1 ELSE 0 END AS target_met
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            ORDER BY w.id DESC
        """, conn)
        conn.close()
        return wl
    except Exception:
        return pd.DataFrame()


def add_to_wishlist(product_id: str, target_price: float):
    conn = sqlite3.connect(DB_PATH)
    # Check if already in wishlist
    exists = conn.execute("SELECT 1 FROM wishlist WHERE product_id=?", (product_id,)).fetchone()
    if exists:
        conn.execute("UPDATE wishlist SET target_price=? WHERE product_id=?", (target_price, product_id))
        msg = "Updated target price in wishlist ✅"
    else:
        conn.execute(
            "INSERT INTO wishlist (product_id, target_price, added_at, alert_sent) VALUES (?,?,?,0)",
            (product_id, target_price, str(date.today()))
        )
        msg = "Added to wishlist ❤️"
    conn.commit()
    conn.close()
    return msg


def remove_from_wishlist(row_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM wishlist WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ── Add Product ────────────────────────────────────────────────────
st.markdown("### ➕ Add a Product to Wishlist")
with st.form("add_wishlist"):
    col_s, col_t = st.columns([3, 1])
    with col_s:
        search = st.text_input("Search product name or brand", placeholder="e.g. boAt, Samsung")
    with col_t:
        st.markdown("<br>", unsafe_allow_html=True)
        searched = st.form_submit_button("🔍 Search")

    results = df.copy()
    if search:
        results = results[results["product_name"].str.contains(search, case=False, na=False)]

    if len(results) == 0:
        st.warning("No products match your search.")
    else:
        options = {f"{row['product_name'][:60]} (₹{row['discounted_price']:,.0f})": row["product_id"]
                   for _, row in results.head(50).iterrows()}
        chosen = st.selectbox("Select product", list(options.keys()))
        chosen_id = options[chosen]
        chosen_row = df[df["product_id"] == chosen_id].iloc[0]

        target = st.number_input(
            "Your Target Price (₹)",
            min_value=1.0,
            max_value=float(chosen_row["actual_price"]) if not pd.isna(chosen_row["actual_price"]) else 999999.0,
            value=float(chosen_row["discounted_price"]) * 0.9,
            step=100.0,
        )
        submitted = st.form_submit_button("❤️ Add to Wishlist")
        if submitted:
            msg = add_to_wishlist(chosen_id, target)
            st.success(msg)
            st.rerun()

# ── Current Wishlist ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 My Wishlist")

wishlist = get_wishlist()

if len(wishlist) == 0:
    st.info("Your wishlist is empty. Search for a product above and add it!")
else:
    # Summary badges
    total = len(wishlist)
    met   = wishlist["target_met"].sum()
    st.markdown(f"**{total}** products tracked · **{met}** at or below your target price 🎯")
    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in wishlist.iterrows():
        with st.container(border=True):
            img_col, info_col, price_col, action_col = st.columns([1, 4, 2, 1])

            with img_col:
                if row["img_link"]:
                    st.image(row["img_link"], use_container_width=True)

            with info_col:
                st.markdown(f"**{row['product_name']}**")
                st.markdown(f"🏢 {row['brand']} · 📂 {row['category_clean']} · ⭐ {row['rating']}")
                st.markdown(f"[View on Amazon →]({row['product_link']})")

            with price_col:
                current  = row["current_price"]
                target   = row["target_price"]
                gap      = current - target
                gap_pct  = gap / current * 100 if current > 0 else 0

                if row["target_met"]:
                    st.markdown(f"<h3 style='color:#10b981; margin:0;'>🎯 Target Met!</h3>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#ef4444;'>₹{gap:,.0f} above target ({gap_pct:.1f}%)</span>", unsafe_allow_html=True)

                st.markdown(f"Current: **₹{current:,.0f}**")
                st.markdown(f"Target:  ₹{target:,.0f}")
                st.markdown(f"Added: {row['added_at']}")

            with action_col:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{row['id']}", help="Remove from wishlist"):
                    remove_from_wishlist(int(row["id"]))
                    st.rerun()
