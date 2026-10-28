import sys
from pathlib import Path

# Ensure dashboard and root directories are in sys.path
_P = Path(__file__).resolve()
for _dir in [_P.parents[1], _P.parents[2], _P.parents[3]]:
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import streamlit as st
import pandas as pd
import numpy as np

try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

st.set_page_config(page_title="Recommendations | BuyWise", page_icon="💡", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">💡 Recommendations</div>', unsafe_allow_html=True)
st.write("Which product gives me the best value right now? Our recommendation engine ranks products to help you decide what to buy.")

# Calculate Scores
df_rec = df.copy()

# 1. Rating Score (40%)
df_rec["rating_score"] = (df_rec["rating"].fillna(0) / 5) * 100

# 2. Discount Score (30%)
df_rec["discount_score"] = df_rec["discount_percentage"].fillna(0)

# 3. Price Score (20%) - Lower price gives a higher score
df_rec["price_score"] = df_rec["discounted_price"].rank(pct=True, ascending=False) * 100

# 4. Review Score (10%) - More reviews gives a higher score
df_rec["review_score"] = df_rec["rating_count"].fillna(0).rank(pct=True) * 100

# Total BuyWise Score
df_rec["buywise_score"] = (
    (df_rec["rating_score"] * 0.40) +
    (df_rec["discount_score"] * 0.30) +
    (df_rec["price_score"] * 0.20) +
    (df_rec["review_score"] * 0.10)
)

def get_recommendation_label(score):
    if score >= 80:
        return "🟢 Best Deal"
    elif score >= 65:
        return "🟡 Good Deal"
    elif score >= 50:
        return "🟠 Average"
    else:
        return "🔴 Not Recommended"

def get_stars(score):
    if score >= 85:
        return "⭐⭐⭐⭐⭐"
    elif score >= 70:
        return "⭐⭐⭐⭐"
    elif score >= 55:
        return "⭐⭐⭐"
    elif score >= 40:
        return "⭐⭐"
    else:
        return "⭐"

df_rec["Recommendation"] = df_rec["buywise_score"].apply(get_recommendation_label)
df_rec["Stars"] = df_rec["buywise_score"].apply(get_stars)

# Filters for user
st.markdown("### Find the Best Deals")
col1, col2 = st.columns(2)
categories = ["All"] + sorted(df_rec["category_clean"].dropna().unique().tolist())
selected_cat = col1.selectbox("Filter by Category", categories)

brands = ["All"] + sorted(df_rec["brand"].dropna().unique().tolist())
selected_brand = col2.selectbox("Filter by Brand", brands)

filtered_df = df_rec.copy()
if selected_cat != "All":
    filtered_df = filtered_df[filtered_df["category_clean"] == selected_cat]
if selected_brand != "All":
    filtered_df = filtered_df[filtered_df["brand"] == selected_brand]

filtered_df = filtered_df.sort_values(by="buywise_score", ascending=False)

st.markdown("---")
if len(filtered_df) == 0:
    st.warning("No products found for the selected filters.")
else:
    st.write(f"Showing the top recommendations from {len(filtered_df)} products.")
    
    # Display top 10 as cards or a table
    top_recs = filtered_df.head(20)
    
    for idx, row in top_recs.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 3, 2, 2])
            
            with c1:
                st.image(row["img_link"], use_container_width=True)
            
            with c2:
                st.markdown(f"**{row['product_name']}**")
                st.markdown(f"Category: {row['category_clean']} | Brand: {row['brand']}")
                st.markdown(f"**Price:** ₹{row['discounted_price']:,.0f} (was ₹{row['actual_price']:,.0f})")
                st.markdown(f"**Discount:** {row['discount_percentage']:.0f}% OFF")
            
            with c3:
                st.markdown("#### BuyWise Score")
                st.markdown(f"<h2 style='color:#6366f1; margin-top:0;'>{row['buywise_score']:.1f}/100</h2>", unsafe_allow_html=True)
                st.markdown(row['Stars'])
            
            with c4:
                st.markdown("#### Verdict")
                st.markdown(f"<h3 style='margin-top:0;'>{row['Recommendation']}</h3>", unsafe_allow_html=True)
                st.markdown(f"Rating: {row['rating']} ⭐ ({row['rating_count']:,.0f} reviews)")
                
        st.markdown("<br>", unsafe_allow_html=True)
