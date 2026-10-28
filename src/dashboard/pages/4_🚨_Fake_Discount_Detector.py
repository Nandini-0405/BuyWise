import streamlit as st
import pandas as pd
import numpy as np
from utils import apply_custom_css, load_data

st.set_page_config(page_title="Fake Discount Detector | BuyWise", page_icon="🚨", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🚨 Fake Discount Detector</div>', unsafe_allow_html=True)
st.write("Identify products where the displayed discount looks suspicious.")

# Add logic for fake discount detection
df_fake = df.copy()

# Calculated Discount = (Actual Price - Selling Price) / Actual Price * 100
# Handle division by zero
df_fake["Calculated Discount (%)"] = np.where(
    df_fake["actual_price"] > 0,
    ((df_fake["actual_price"] - df_fake["discounted_price"]) / df_fake["actual_price"]) * 100,
    0
)

# Difference between listed and calculated discount
df_fake["Discount Difference"] = df_fake["discount_percentage"] - df_fake["Calculated Discount (%)"]

# Find suspicious discounts (difference of more than 1%)
suspicious = df_fake[df_fake["Discount Difference"].abs() > 1.0].copy()

# Metrics
total_products = len(df_fake)
suspicious_count = len(suspicious)
suspicious_rate = (suspicious_count / total_products) * 100 if total_products > 0 else 0

col1, col2, col3 = st.columns(3)
col1.markdown(f'<div class="metric-card"><div class="metric-label">Total Products Analyzed</div><div class="metric-value">{total_products:,}</div></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="metric-card"><div class="metric-label">Suspicious Discounts Found</div><div class="metric-value">{suspicious_count:,}</div></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="metric-card"><div class="metric-label">Suspicious Rate</div><div class="metric-value">{suspicious_rate:.1f}%</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("### 🚨 Suspicious Discounts")

if suspicious_count > 0:
    display_cols = ["product_name", "actual_price", "discounted_price", "discount_percentage", "Calculated Discount (%)", "Discount Difference"]
    display_df = suspicious[display_cols].sort_values(by="Discount Difference", ascending=False)
    
    display_df["actual_price"] = display_df["actual_price"].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
    display_df["discounted_price"] = display_df["discounted_price"].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
    display_df["discount_percentage"] = display_df["discount_percentage"].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")
    display_df["Calculated Discount (%)"] = display_df["Calculated Discount (%)"].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")
    display_df["Discount Difference"] = display_df["Discount Difference"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
    
    display_df = display_df.rename(columns={
        "product_name": "Product",
        "actual_price": "MRP",
        "discounted_price": "Selling Price",
        "discount_percentage": "Listed Discount",
        "Calculated Discount (%)": "Calculated Discount",
        "Discount Difference": "Difference"
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.success("No suspicious discounts detected! All listed discounts roughly match the calculated discounts.")

st.markdown("---")
st.markdown("### 🔮 Coming Soon: Historical Price Tracking")
st.info("""
**When historical prices become available, this detection will get MUCH better:**

*   **30 days ago:** ₹8,500
*   **15 days ago:** ₹9,000
*   **Sale price:** ₹8,700

We'll be able to detect whether the "sale" price is actually a good deal compared to recent trends, rather than just trusting the MRP.
""")
