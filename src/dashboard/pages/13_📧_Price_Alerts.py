"""
BuyWise - Price Alerts Page
Set a target price for any wishlist product.
Get email notifications via free Gmail SMTP when the price drops.
"""

import sqlite3
import smtplib
import streamlit as st
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import apply_custom_css, load_data

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import (
    DB_PATH,
    ALERT_EMAIL_SENDER,
    ALERT_EMAIL_PASSWORD,
    ALERT_EMAIL_HOST,
    ALERT_EMAIL_PORT,
)

st.set_page_config(page_title="Price Alerts | BuyWise", page_icon="📧", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">📧 Price Alerts</div>', unsafe_allow_html=True)
st.write("Get notified by email the moment a product hits your target price.")

# ── Email Config Check ─────────────────────────────────────────────
email_configured = bool(ALERT_EMAIL_SENDER and ALERT_EMAIL_PASSWORD)

if not email_configured:
    st.warning("""
    ⚙️ **Email not configured yet.**  
    To enable real email alerts, set these environment variables:
    ```
    BUYWISE_EMAIL_SENDER=your.gmail@gmail.com
    BUYWISE_EMAIL_PASSWORD=your_app_password_here
    ```
    Get a Gmail App Password at: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)  
    *(Enable 2-Step Verification first, then generate an App Password for "Mail")*
    """)

# ── Send Email Helper ──────────────────────────────────────────────

def send_alert_email(to_email: str, product_name: str, current_price: float, target_price: float, product_link: str) -> bool:
    """Send price drop alert via Gmail SMTP. Returns True on success."""
    if not email_configured:
        return False

    subject = f"🎉 Price Drop Alert: {product_name[:50]}"
    body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #111;">
    <div style="max-width:600px; margin:auto; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden;">
        <div style="background:#6366f1; padding:20px; color:white;">
            <h2 style="margin:0;">🎯 BuyWise Price Alert</h2>
        </div>
        <div style="padding:24px;">
            <p>Good news! A product on your BuyWise wishlist has hit your target price.</p>
            <h3 style="color:#111;">{product_name}</h3>
            <table style="width:100%; border-collapse:collapse; margin:16px 0;">
                <tr style="background:#f9fafb;">
                    <td style="padding:10px; font-weight:bold;">Your Target Price</td>
                    <td style="padding:10px; color:#6366f1; font-size:1.4rem; font-weight:bold;">₹{target_price:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding:10px; font-weight:bold;">Current Price</td>
                    <td style="padding:10px; color:#10b981; font-size:1.4rem; font-weight:bold;">₹{current_price:,.0f}</td>
                </tr>
            </table>
            <a href="{product_link}" style="display:inline-block; background:#6366f1; color:white;
               padding:12px 24px; border-radius:6px; text-decoration:none; font-weight:bold;">
                🛒 Buy on Amazon Now
            </a>
            <p style="color:#9ca3af; font-size:0.8rem; margin-top:24px;">
                Sent by BuyWise — Your Smart Shopping Intelligence Platform
            </p>
        </div>
    </div>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = ALERT_EMAIL_SENDER
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(ALERT_EMAIL_HOST, ALERT_EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(ALERT_EMAIL_SENDER, ALERT_EMAIL_PASSWORD)
            server.sendmail(ALERT_EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False


# ── Load Wishlist ──────────────────────────────────────────────────

def get_wishlist_alerts() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        wl = pd.read_sql("""
            SELECT w.id, w.product_id, p.product_name, p.discounted_price AS current_price,
                   p.actual_price, p.img_link, p.product_link, p.rating,
                   w.target_price, w.added_at, w.alert_sent
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            ORDER BY w.id DESC
        """, conn)
        conn.close()
        return wl
    except Exception:
        return pd.DataFrame()


wishlist = get_wishlist_alerts()

# ── Set Alert on New Product ───────────────────────────────────────
st.markdown("### 🔔 Set a New Price Alert")

with st.form("alert_form"):
    col_s, col_e = st.columns(2)
    search_q = col_s.text_input("Search product", placeholder="e.g. Headphones, Laptop")
    alert_email = col_e.text_input("Your Email", placeholder="you@gmail.com")

    search_results = df.copy()
    if search_q:
        search_results = search_results[search_results["product_name"].str.contains(search_q, case=False, na=False)]

    if len(search_results) > 0:
        options = {f"{r['product_name'][:60]} (₹{r['discounted_price']:,.0f})": i
                   for i, r in search_results.head(50).iterrows()}
        chosen_label = st.selectbox("Select product", list(options.keys()))
        chosen_idx = options[chosen_label]
        chosen_row = df.loc[chosen_idx]

        current = chosen_row["discounted_price"]
        target_p = st.number_input(
            "Alert me when price drops to (₹)",
            min_value=1.0,
            max_value=float(current),
            value=float(current) * 0.85,
            step=100.0,
        )

        if st.form_submit_button("🔔 Set Alert"):
            # Add to wishlist table with the target
            conn = sqlite3.connect(DB_PATH)
            exists = conn.execute("SELECT 1 FROM wishlist WHERE product_id=?", (chosen_row["product_id"],)).fetchone()
            from datetime import date
            if exists:
                conn.execute("UPDATE wishlist SET target_price=?, alert_sent=0 WHERE product_id=?",
                             (target_p, chosen_row["product_id"]))
            else:
                conn.execute("INSERT INTO wishlist (product_id, target_price, added_at, alert_sent) VALUES (?,?,?,0)",
                             (chosen_row["product_id"], target_p, str(date.today())))
            conn.commit()
            conn.close()
            st.success(f"✅ Alert set for ₹{target_p:,.0f}! We'll email {alert_email} when the price drops.")

# ── Active Alerts ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔔 Active Alerts")

if len(wishlist) == 0:
    st.info("No alerts set yet. Search for a product above to set your first alert.")
else:
    targets_met = wishlist[wishlist["current_price"] <= wishlist["target_price"]]
    if len(targets_met) > 0:
        st.success(f"🎯 **{len(targets_met)} product(s) have hit your target price right now!**")

    for _, row in wishlist.iterrows():
        with st.container(border=True):
            img_c, info_c, status_c = st.columns([1, 4, 2])

            with img_c:
                if row["img_link"]:
                    st.image(row["img_link"], use_container_width=True)

            with info_c:
                st.markdown(f"**{row['product_name']}**")
                st.markdown(f"Current: **₹{row['current_price']:,.0f}** | Target: ₹{row['target_price']:,.0f}")
                st.markdown(f"Rating: {row['rating']} ⭐ | Set on: {row['added_at']}")

            with status_c:
                if row["current_price"] <= row["target_price"]:
                    st.markdown("### 🎯 Target Met!")
                    if email_configured:
                        if st.button("📧 Send Alert Email", key=f"send_{row['id']}"):
                            sent = send_alert_email(
                                ALERT_EMAIL_SENDER,
                                row["product_name"],
                                row["current_price"],
                                row["target_price"],
                                row["product_link"],
                            )
                            if sent:
                                st.success("Email sent!")
                    st.markdown(f"[Buy Now →]({row['product_link']})")
                else:
                    gap = row["current_price"] - row["target_price"]
                    gap_pct = gap / row["current_price"] * 100
                    st.markdown(f"<span style='color:#ef4444;'>₹{gap:,.0f} above target ({gap_pct:.1f}% to go)</span>", unsafe_allow_html=True)
                    st.progress(min(1.0, row["target_price"] / row["current_price"]))

# ── How to Enable Automated Alerts ────────────────────────────────
st.markdown("---")
with st.expander("📖 How to enable automated email alerts"):
    st.markdown("""
    BuyWise can **automatically** email you every day if any wishlist price drops to your target.  
    The daily pipeline checks all wishlist items after scraping.

    **Setup steps:**
    1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
    2. Create an App Password for **Mail**
    3. Create a `.env` file in the project root:
       ```
       BUYWISE_EMAIL_SENDER=your.gmail@gmail.com
       BUYWISE_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
       ```
    4. Run `python src/etl/pipeline.py` — it will check prices and email you automatically.
    """)
