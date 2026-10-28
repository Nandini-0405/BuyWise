import sys
from pathlib import Path

# Ensure dashboard and root directories are in sys.path
_P = Path(__file__).resolve()
for _dir in [_P.parents[1], _P.parents[2], _P.parents[3]]:
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import streamlit as st
import math
try:
    from utils import apply_custom_css, load_data
except (ImportError, AttributeError):
    from src.dashboard.utils import apply_custom_css, load_data

st.set_page_config(page_title="Product Explorer | BuyWise", page_icon="🔍", layout="wide")
apply_custom_css()
df = load_data()

st.markdown('<div class="section-title">🔍 Product Explorer</div>', unsafe_allow_html=True)

# --------------------------------------------------
# Filters (Sidebar)
# --------------------------------------------------
st.sidebar.header("Filters")

categories = ["All"] + sorted(df["category_clean"].dropna().unique().tolist())
selected_cat = st.sidebar.selectbox("Category", categories)

brands = ["All"] + sorted(df["brand"].dropna().unique().tolist())
selected_brand = st.sidebar.selectbox("Brand", brands)

min_p, max_p = float(df["discounted_price"].min()), float(df["discounted_price"].max())
if math.isnan(min_p): min_p = 0.0
if math.isnan(max_p): max_p = 100000.0

price_range = st.sidebar.slider("Price Range (₹)", min_value=0, max_value=int(max_p), value=(0, int(max_p)), step=100)

rating_filter = st.sidebar.selectbox("Minimum Rating", ["Any", "4.5+", "4.0+", "3.5+", "3.0+"])

discount_filter = st.sidebar.slider("Minimum Discount (%)", 0, 100, 0, step=5)

# --------------------------------------------------
# Main Search Bar
# --------------------------------------------------
search_term = st.text_input("🔍 Search for a product...", placeholder="e.g. Headphones, iPhone, Samsung...")

# --------------------------------------------------
# Apply Filters
# --------------------------------------------------
filtered = df.copy()

if search_term:
    filtered = filtered[filtered["product_name"].str.contains(search_term, case=False, na=False)]

if selected_cat != "All":
    filtered = filtered[filtered["category_clean"] == selected_cat]

if selected_brand != "All":
    filtered = filtered[filtered["brand"] == selected_brand]

filtered = filtered[(filtered["discounted_price"] >= price_range[0]) & (filtered["discounted_price"] <= price_range[1])]

rating_map = {"4.5+": 4.5, "4.0+": 4.0, "3.5+": 3.5, "3.0+": 3.0}
if rating_filter in rating_map:
    filtered = filtered[filtered["rating"] >= rating_map[rating_filter]]

filtered = filtered[filtered["discount_percentage"] >= discount_filter]


# --------------------------------------------------
# Product Details Dialog
# --------------------------------------------------
@st.dialog("Product Details", width="large")
def show_product_details(product):
    st.markdown(f"### {product['product_name']}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(product["img_link"], use_container_width=True)
        st.markdown(f"**[View on Amazon]({product['product_link']})**")
        
    with col2:
        st.markdown(f"**Brand:** {product['brand']}")
        st.markdown(f"**Category:** {product['category_clean']}")
        st.markdown(f"**Rating:** {product['rating']} ⭐ ({product['rating_count']:,} reviews)")
        st.markdown(f"**Current Price:** ₹{product['discounted_price']:,.2f}")
        st.markdown(f"**Original Price:** ₹{product['actual_price']:,.2f} <span style='color:red;'>({product['discount_percentage']}% OFF)</span>", unsafe_allow_html=True)
        st.markdown(f"**Savings:** ₹{product['discount_amount']:,.2f}")
        
    st.markdown("---")
    st.markdown("#### Description")
    # Clean up the description a bit
    desc = str(product['about_product']).replace('|', '\\n- ')
    st.markdown(f"- {desc}")

def render_product_grid(df_to_render, key_prefix):
    if len(df_to_render) == 0:
        st.warning("No products found.")
        return
        
    cols = st.columns(4)
    for idx, row in df_to_render.iterrows():
        col = cols[idx % 4]
        with col:
            with st.container(border=True):
                st.image(row["img_link"], use_container_width=True)
                title = row['product_name']
                if len(title) > 40:
                    title = title[:37] + "..."
                st.markdown(f"**{title}**")
                
                st.markdown(f"⭐ {row['rating']}")
                st.markdown(f"**₹{row['discounted_price']:,.0f}** <span style='color:red;font-size:0.8rem;'>{row['discount_percentage']}% OFF</span>", unsafe_allow_html=True)
                
                if st.button("View Product →", key=f"btn_{key_prefix}_{row['product_id']}_{idx}"):
                    show_product_details(row)

# --------------------------------------------------
# Recommended Products Section
# --------------------------------------------------
if not search_term:
    st.markdown("### ⭐ Recommended for You")
    # Recommendations: High rating, high discount, mostly from the selected category if filtered
    recs = filtered[(filtered["rating"] >= 4.2) & (filtered["discount_percentage"] > 30)]
    if len(recs) < 4:
        recs = df[(df["rating"] >= 4.0)].head(4) # Fallback to general if filters are too strict
    recs = recs.sort_values(by="rating_count", ascending=False).head(4)
    
    render_product_grid(recs, "rec")
    st.markdown("---")
    st.markdown("### All Products")

st.write(f"Showing **{len(filtered)}** products")

# --------------------------------------------------
# Main Product Grid
# --------------------------------------------------
display_df = filtered.head(50)
render_product_grid(display_df, "main")

