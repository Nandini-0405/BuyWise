-- ============================================
-- BuyWise Database Schema (Full Version)
-- ============================================

-- Products snapshot table (latest state of each product)
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id          TEXT PRIMARY KEY,
    product_name        TEXT,
    category            TEXT,
    category_clean      TEXT,
    brand               TEXT,
    discounted_price    REAL,
    actual_price        REAL,
    discount_percentage REAL,
    discount_amount     REAL,
    rating              REAL,
    rating_count        INTEGER,
    about_product       TEXT,
    review_title        TEXT,
    review_content      TEXT,
    img_link            TEXT,
    product_link        TEXT,
    last_updated        TEXT    -- ISO date of last scrape
);

-- Price history table (one row per product per day)
DROP TABLE IF EXISTS price_history;

CREATE TABLE price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      TEXT    NOT NULL,
    scraped_at      TEXT    NOT NULL,   -- ISO date e.g. 2025-10-24
    price           REAL,
    actual_price    REAL,
    discount_pct    REAL,
    in_stock        INTEGER DEFAULT 1,  -- 1 = in stock, 0 = out of stock
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Wishlist table (user-tracked products)
DROP TABLE IF EXISTS wishlist;

CREATE TABLE wishlist (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      TEXT    NOT NULL,
    target_price    REAL,               -- user's desired price
    added_at        TEXT    NOT NULL,
    alert_sent      INTEGER DEFAULT 0,  -- 1 = email alert already sent
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date    ON price_history(scraped_at);
CREATE INDEX IF NOT EXISTS idx_wishlist_product      ON wishlist(product_id);