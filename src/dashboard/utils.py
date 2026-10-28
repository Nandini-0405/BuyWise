import sqlite3
import pandas as pd
import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
        }

        /* Modern Background */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            color: #1f2937;
        }

        /* Remove default top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Header Styling */
        .bw-header {
            margin-bottom: 2.5rem;
            padding: 1.5rem;
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            border-radius: 16px;
            color: white;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            animation: fadeInDown 0.8s ease-out;
        }
        .bw-header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .bw-header p {
            font-size: 1.1rem;
            color: #f3f4f6;
            font-weight: 400;
            margin: 0.5rem 0 0 0;
        }

        /* Metric cards with Glassmorphism and Hover */
        .metric-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border-color: #6366f1;
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.03em;
            background: linear-gradient(90deg, #111827, #374151);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-sub {
            font-size: 0.85rem;
            font-weight: 500;
            color: #9ca3af;
            margin-top: 0.4rem;
        }

        /* Section titles */
        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
            display: inline-block;
            position: relative;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 40px;
            height: 2px;
            background: #6366f1;
        }

        /* Input fields and selectboxes */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div {
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            background: #ffffff;
            font-size: 1rem;
            color: #111827;
            padding: 0.7rem 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div:focus-within {
            border-color: #6366f1;
            box-shadow: 0 0 0 4px rgba(99,102,241,0.15) !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
        }
        .stButton > button:hover {
            transform: scale(1.02) translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
            color: white;
        }

        /* Streamlit generic containers (for product cards) */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            background: #ffffff;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        /* Animations */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translate3d(0, -20px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        /* Hide Streamlit chrome */
        #MainMenu, footer, header { visibility: hidden; }
        .stDeployButton { display: none; }
        div[data-testid="stDecoration"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

from pathlib import Path

@st.cache_data
def load_data():
    db_path = Path(__file__).resolve().parent.parent.parent / "database" / "buywise.db"
    if not db_path.exists():
        db_path = Path("database/buywise.db")
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()

    # --- prices ---
    for col in ["discounted_price", "actual_price"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("₹", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- discount % ---
    df["discount_percentage"] = (
        df["discount_percentage"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce")

    # --- rating ---
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # --- rating count ---
    df["rating_count"] = (
        df["rating_count"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce")

    # --- CALCULATED: discount amount ---
    df["discount_amount"] = (df["actual_price"] - df["discounted_price"]).round(2)

    # --- clean category (take top-level only) ---
    df["category_clean"] = df["category"].astype(str).str.split("|").str[0].str.strip()

    # --- extract brand ---
    df["brand"] = df["product_name"].astype(str).str.split(" ").str[0].str.strip()

    return df
