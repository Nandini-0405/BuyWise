import streamlit as st
import pandas as pd
from utils import apply_custom_css, load_data

st.set_page_config(page_title="Product Comparison | BuyWise", page_icon="⚖️", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">⚖️ Product Comparison</div>', unsafe_allow_html=True)
st.write("Compare 2 to 4 products side-by-side to find the best deal.")

# --------------------------------------------------
# Selection
# --------------------------------------------------
# Create a dictionary mapping product names to IDs to handle duplicate names safely
product_names = df["product_name"].tolist()
product_ids = df["product_id"].tolist()
name_to_id = {f"{name} ({pid})": pid for name, pid in zip(product_names, product_ids)}

selected_options = st.multiselect(
    "Search and select products to compare:",
    options=list(name_to_id.keys()),
    max_selections=4,
    placeholder="Choose up to 4 products..."
)

# --------------------------------------------------
# Comparison Logic
# --------------------------------------------------
if len(selected_options) < 2:
    st.info("ℹ️ Please select at least 2 products to see the comparison and verdict.")
else:
    # Filter the dataframe for selected products
    selected_ids = [name_to_id[opt] for opt in selected_options]
    
    # We use set_index to ensure the order matches the selection order or we can just iterate over selected_ids
    compare_df = df[df["product_id"].isin(selected_ids)].copy()
    
    # Calculate BuyWise Value Score
    # Simple heuristic: Higher rating is good, higher discount is good, lower price is good (relative to category)
    # Let's use a straightforward formula: (Rating * 20) + Discount Percentage
    compare_df["value_score"] = (compare_df["rating"] * 20) + compare_df["discount_percentage"]
    
    best_product = compare_df.sort_values(by="value_score", ascending=False).iloc[0]
    
    # Verdict Section
    st.markdown("---")
    st.markdown("### BuyWise Verdict")
    st.success(f"🏆 **{best_product['product_name'][:60]}...** offers the best current value among your choices based on its price, rating ({best_product['rating']} ⭐), and discount ({best_product['discount_percentage']}%).")
    st.markdown("---")
    
    # Side-by-side layout
    cols = st.columns(len(selected_ids))
    
    for idx, pid in enumerate(selected_ids):
        # Get the row for this product
        row = compare_df[compare_df["product_id"] == pid].iloc[0]
        
        with cols[idx]:
            with st.container(border=True):
                # Image
                st.image(row["img_link"], use_container_width=True)
                
                # Title
                title = row['product_name']
                if len(title) > 60: title = title[:57] + "..."
                st.markdown(f"**{title}**")
                
                # Price & Discount
                st.markdown(f"### ₹{row['discounted_price']:,.0f}")
                st.markdown(f"~~₹{row['actual_price']:,.0f}~~ <span style='color:red; font-weight:bold;'>({row['discount_percentage']}% OFF)</span>", unsafe_allow_html=True)
                
                # Stats
                st.markdown(f"**⭐ Rating:** {row['rating']} ({row['rating_count']:,} reviews)")
                st.markdown(f"**🏢 Brand:** {row['brand']}")
                st.markdown(f"**📂 Category:** {row['category_clean']}")
                
                # Link
                st.markdown(f"[View on Amazon →]({row['product_link']})")
