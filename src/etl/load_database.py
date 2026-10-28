"""
BuyWise - Incremental Database Updater
Upserts product data and appends a new price_history row per product per run.
Run this after scraping to persist live Amazon data.
"""

import sqlite3
import logging
from datetime import date

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH

log = logging.getLogger("buywise.db_updater")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def init_db():
    """Create tables from schema.sql if they don't exist yet."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"
    conn = sqlite3.connect(DB_PATH)
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    log.info("Database initialized / verified.")


def upsert_product(conn: sqlite3.Connection, product: dict):
    """
    Insert a product if it doesn't exist, or update it if the price/rating changed.
    Uses SQLite's INSERT OR REPLACE which acts as an upsert on PRIMARY KEY.
    """
    conn.execute("""
        INSERT OR REPLACE INTO products (
            product_id, product_name, category, category_clean, brand,
            discounted_price, actual_price, discount_percentage, discount_amount,
            rating, rating_count, about_product, review_title, review_content,
            img_link, product_link, last_updated
        ) VALUES (
            :product_id, :product_name, :category, :category_clean, :brand,
            :discounted_price, :actual_price, :discount_percentage, :discount_amount,
            :rating, :rating_count, :about_product, :review_title, :review_content,
            :img_link, :product_link, :last_updated
        )
    """, product)


def append_price_history(conn: sqlite3.Connection, product: dict):
    """
    Append one price history row for today.
    Skips if a row for this product_id + today already exists (idempotent).
    """
    today = str(date.today())
    exists = conn.execute(
        "SELECT 1 FROM price_history WHERE product_id=? AND scraped_at=?",
        (product["product_id"], today)
    ).fetchone()

    if exists:
        log.info(f"Price history for {product['product_id']} already recorded today — skipping.")
        return

    conn.execute("""
        INSERT INTO price_history (product_id, scraped_at, price, actual_price, discount_pct, in_stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        product["product_id"],
        today,
        product.get("discounted_price"),
        product.get("actual_price"),
        product.get("discount_percentage"),
        1,
    ))


def save_products(products: list[dict]):
    """
    Main entry point: upsert all products + append price history rows.

    Args:
        products: List of product dicts from amazon_scraper.scrape_products_bulk()
    """
    if not products:
        log.warning("No products to save.")
        return

    conn = sqlite3.connect(DB_PATH)

    inserted = 0
    history_added = 0

    for p in products:
        try:
            upsert_product(conn, p)
            inserted += 1
            append_price_history(conn, p)
            history_added += 1
        except Exception as e:
            log.error(f"Failed to save {p.get('product_id')}: {e}")

    conn.commit()
    conn.close()

    log.info(f"✅ Upserted {inserted} products | Added {history_added} price history rows.")


def load_products_from_csv(csv_path: str):
    """
    Utility to bulk-load from a processed CSV into the new schema.
    Use this once to migrate your existing data into the updated DB.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Clean price columns (remove ₹ and commas if they're strings)
    for col in ["discounted_price", "actual_price", "discount_percentage", "rating", "rating_count"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace("₹", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add computed columns if missing
    if "discount_amount" not in df.columns and "actual_price" in df.columns and "discounted_price" in df.columns:
        df["discount_amount"] = df["actual_price"] - df["discounted_price"]

    if "brand" not in df.columns:
        df["brand"] = ""
    if "category_clean" not in df.columns:
        df["category_clean"] = df.get("category", "")
    if "last_updated" not in df.columns:
        df["last_updated"] = str(date.today())

    products = df.to_dict(orient="records")
    log.info(f"Loading {len(products)} products from CSV…")
    save_products(products)


if __name__ == "__main__":
    import sys
    init_db()
    if len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
        load_products_from_csv(sys.argv[1])
    else:
        print("Usage: python load_database.py data/processed/your_file.csv")
        print("Or import save_products() from your scraper pipeline.")