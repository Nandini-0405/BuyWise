"""
BuyWise - Database Migration
Run this ONCE to:
1. Apply the new schema (adds price_history and wishlist tables)
2. Migrate all existing products from the current DB into the new schema
3. Seed one day of price history from today's prices

Usage:
    python migrate_db.py
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("buywise.migrate")

DB_PATH     = Path("database/buywise.db")
SCHEMA_PATH = Path("database/schema.sql")


def migrate():
    log.info("Starting database migration...")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Check what columns exist in products ──────────────────────
    cur.execute("PRAGMA table_info(products)")
    existing_cols = {row[1] for row in cur.fetchall()}
    log.info(f"Existing columns: {existing_cols}")

    # ── Add missing columns to products (non-destructive) ─────────
    new_cols = {
        "category_clean": "TEXT",
        "brand":          "TEXT",
        "discount_amount": "REAL",
        "last_updated":   "TEXT",
    }

    for col, col_type in new_cols.items():
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE products ADD COLUMN {col} {col_type}")
            log.info(f"Added column: products.{col}")

    # ── Create new tables if they don't exist ─────────────────────
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS price_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id   TEXT NOT NULL,
            scraped_at   TEXT NOT NULL,
            price        REAL,
            actual_price REAL,
            discount_pct REAL,
            in_stock     INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS wishlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id   TEXT NOT NULL,
            target_price REAL,
            added_at     TEXT NOT NULL,
            alert_sent   INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_ph_product ON price_history(product_id);
        CREATE INDEX IF NOT EXISTS idx_ph_date    ON price_history(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_wl_product ON wishlist(product_id);
    """)

    # ── Backfill derived columns ───────────────────────────────────
    import re
    from datetime import date

    # Clean up discount_percentage if stored as '80%'
    cur.execute("SELECT product_id, discount_percentage FROM products WHERE discount_percentage IS NOT NULL")
    rows = cur.fetchall()
    for pid, disc in rows:
        if isinstance(disc, str):
            cleaned = re.sub(r"[^\d.]", "", disc)
            try:
                cur.execute("UPDATE products SET discount_percentage=? WHERE product_id=?", (float(cleaned), pid))
            except Exception:
                pass

    # Backfill discount_amount
    cur.execute("""
        UPDATE products
        SET discount_amount = actual_price - discounted_price
        WHERE discount_amount IS NULL AND actual_price IS NOT NULL AND discounted_price IS NOT NULL
    """)

    # Backfill category_clean (last segment of category)
    cur.execute("SELECT product_id, category FROM products WHERE category_clean IS NULL OR category_clean = ''")
    for pid, cat in cur.fetchall():
        if cat:
            clean = cat.split("|")[-1].split(">")[-1].strip()
        else:
            clean = "Uncategorized"
        cur.execute("UPDATE products SET category_clean=? WHERE product_id=?", (clean, pid))

    # Backfill brand from product_name (rough heuristic)
    cur.execute("SELECT product_id, product_name FROM products WHERE brand IS NULL OR brand = ''")
    for pid, name in cur.fetchall():
        brand = name.split()[0] if name else ""
        cur.execute("UPDATE products SET brand=? WHERE product_id=?", (brand, pid))

    # Backfill last_updated
    today = str(date.today())
    cur.execute("UPDATE products SET last_updated=? WHERE last_updated IS NULL", (today,))

    # ── Seed price_history with today's snapshot ──────────────────
    cur.execute("SELECT COUNT(*) FROM price_history")
    existing_history = cur.fetchone()[0]

    if existing_history == 0:
        log.info("Seeding price_history with today's prices...")
        cur.execute("""
            INSERT INTO price_history (product_id, scraped_at, price, actual_price, discount_pct, in_stock)
            SELECT product_id, ?, discounted_price, actual_price, discount_percentage, 1
            FROM products
            WHERE discounted_price IS NOT NULL
        """, (today,))
        inserted = cur.rowcount
        log.info(f"Seeded {inserted} price history rows.")
    else:
        log.info(f"price_history already has {existing_history} rows — skipping seed.")

    conn.commit()
    conn.close()
    log.info("✅ Migration complete!")


if __name__ == "__main__":
    migrate()
