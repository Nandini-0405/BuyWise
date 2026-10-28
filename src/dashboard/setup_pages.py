import os

pages_dir = r'c:\Users\nandi\OneDrive\Desktop\BuyWise\src\dashboard\pages'

# Mapping of old names to new names (if applicable)
renames = {
    '1_🔍_Product_Explorer.py': '1_🔍_Product_Explorer.py',
    '3_🏢_Brand_Analysis.py': '5_🏢_Brand_Analysis.py',
    '4_📂_Category_Analysis.py': '6_📂_Category_Analysis.py',
    '6_📊_Insights.py': '14_📊_Market_Insights.py',
}

# The files that need to be created (empty boilerplate)
new_files = [
    '2_⚖️_Product_Comparison.py',
    '4_🚨_Fake_Discount_Detector.py',
    '7_📈_Price_History.py',
    '8_🎉_Festival_Analysis.py',
    '9_🕒_Best_Time_to_Buy.py',
    '10_🤖_Price_Prediction.py',
    '11_❤️_Wishlist.py',
    '12_💰_Savings_Calculator.py',
    '13_📧_Price_Alerts.py',
]

# Rename existing ones
for old, new in renames.items():
    old_path = os.path.join(pages_dir, old)
    new_path = os.path.join(pages_dir, new)
    if os.path.exists(old_path) and old_path != new_path:
        os.rename(old_path, new_path)

rec_path = os.path.join(pages_dir, '5_⭐_Recommendations.py')
if os.path.exists(rec_path):
    os.remove(rec_path)

# Create new files with boilerplate
for f in new_files:
    f_path = os.path.join(pages_dir, f)
    if not os.path.exists(f_path):
        title = f.split('_', 2)[-1].replace('_', ' ').replace('.py', '')
        emoji = f.split('_')[1]
        with open(f_path, 'w', encoding='utf-8') as out:
            out.write(f'''import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import apply_custom_css
except ImportError:
    apply_custom_css = lambda: None

st.set_page_config(page_title="{title}", page_icon="{emoji}", layout="wide")
apply_custom_css()

st.title("{emoji} {title}")
st.write("This page is under construction.")
''')

