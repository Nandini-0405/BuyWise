# BuyWise 🛍️
> **Smart Shopping Intelligence & Price Analytics Platform**

BuyWise is an end-to-end data intelligence and shopping assistant platform that tracks e-commerce trends, detects artificial/fake discounts, forecasts price drops, and suggests smart buying recommendations.

---

## 🚀 Live Cloud Deployment (Streamlit Community Cloud - 100% Free)

You can host BuyWise online 24/7 so anyone in the world can access and interact with it:

### Step 1: Push your project to GitHub
1. Create a new public repository on [GitHub](https://github.com/new) named `BuyWise`.
2. Link your local project and push:
```bash
git remote add origin https://github.com/<YOUR-USERNAME>/BuyWise.git
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Visit **[share.streamlit.io](https://share.streamlit.io)** and sign in with your GitHub account.
2. Click **"New app"**.
3. Fill in the deployment details:
   - **Repository**: `<YOUR-USERNAME>/BuyWise`
   - **Branch**: `main`
   - **Main file path**: `src/dashboard/app.py`
   - **App URL**: Choose a custom subdomain (e.g., `buywise-shopping.streamlit.app`)
4. Click **Deploy!**

Your app will be live and accessible to anyone worldwide in ~2 minutes!

---

## 💻 Running Locally

To run the application locally on your computer:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the Streamlit dashboard
streamlit run src/dashboard/app.py
```
Or simply run:
```bash
python main.py
```

---

## 🌟 Key Features

- **🔍 Product Explorer**: Search, filter, and inspect detailed catalog items.
- **⚖️ Product Comparison**: Side-by-side spec, pricing, and rating comparisons.
- **💰 Discount Intelligence**: Identify real value drops vs inflated prices.
- **🚨 Fake Discount Detector**: Detect deceptive price inflation practices.
- **🏢 Brand & Category Analytics**: In-depth market breakdown across categories.
- **📈 Price History & Trends**: Historical tracking of pricing changes.
- **🎉 Festival Analysis**: Big billion days & festive sale price patterns.
- **🕒 Best Time to Buy**: Smart timing recommendations.
- **🤖 Price Prediction**: Machine learning-based future price forecasts.
- **❤️ Wishlist & Savings Calculator**: Target purchase trackers with instant savings calculations.
- **📧 Price Drop Alerts**: Email notifications when prices hit target thresholds.

---

## 🛠️ Tech Stack

- **Frontend & UI**: Streamlit, Plotly, HTML/CSS
- **Backend & ML**: Python, Scikit-learn, Pandas, NumPy
- **Database**: SQLite, SQLAlchemy
- **Data Pipeline**: Custom scrapers & ETL pipeline