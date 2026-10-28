"""
BuyWise - Amazon India Scraper
Fetches live product data from Amazon.in using product ASINs.
Free – no API key required.

Usage:
    from src.etl.amazon_scraper import scrape_product, scrape_products_bulk

    product = scrape_product("B0CHX3QBCH")   # single ASIN
    results = scrape_products_bulk(asins)     # list of ASINs
"""

import time
import random
import logging
import sqlite3
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    USER_AGENTS,
    AMAZON_BASE_URL,
    SCRAPER_DELAY_MIN,
    SCRAPER_DELAY_MAX,
    SCRAPER_TIMEOUT,
    DB_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("buywise.scraper")


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _get_headers() -> dict:
    """Return headers that mimic a real browser, rotating User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
    }


def _clean_price(raw: str) -> float | None:
    """Convert '₹1,23,456' → 123456.0"""
    if not raw:
        return None
    cleaned = re.sub(r"[₹,\s]", "", raw).strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_number(raw: str) -> float | None:
    """Parse rating count like '1,234' or '4,567 ratings'."""
    if not raw:
        return None
    digits = re.sub(r"[^\d.]", "", raw)
    try:
        return float(digits)
    except ValueError:
        return None


def _safe_text(tag) -> str:
    """Return stripped text from a BeautifulSoup tag, or empty string."""
    return tag.get_text(strip=True) if tag else ""


# ──────────────────────────────────────────────────────────────────
# Core Scraper
# ──────────────────────────────────────────────────────────────────

def scrape_product(asin: str) -> dict | None:
    """
    Scrape one Amazon India product page by ASIN.

    Returns a dict matching the `products` DB schema, or None on failure.
    """
    url = f"{AMAZON_BASE_URL}/dp/{asin}"
    log.info(f"Scraping ASIN: {asin}  →  {url}")

    try:
        resp = requests.get(url, headers=_get_headers(), timeout=SCRAPER_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Request failed for {asin}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # ── Product Name ──────────────────────────────────────────────
    name_tag = (
        soup.find("span", id="productTitle") or
        soup.find("h1", {"data-automation-id": "title"})
    )
    product_name = _safe_text(name_tag)

    if not product_name:
        log.warning(f"Could not parse product name for {asin}. Possibly blocked.")
        return None

    # ── Prices ───────────────────────────────────────────────────
    # Discounted / sale price
    price_tag = (
        soup.find("span", class_="a-price-whole") or
        soup.find("span", {"id": "priceblock_ourprice"}) or
        soup.find("span", {"id": "priceblock_dealprice"})
    )
    discounted_price = _clean_price(_safe_text(price_tag))

    # MRP / actual price
    mrp_block = soup.find("span", class_="a-price a-text-price")
    actual_price = None
    if mrp_block:
        mrp_tag = mrp_block.find("span", class_="a-offscreen")
        actual_price = _clean_price(_safe_text(mrp_tag))

    # Fallback: if no MRP found, actual = discounted
    if actual_price is None:
        actual_price = discounted_price

    # Discount percentage
    discount_pct = None
    if actual_price and discounted_price and actual_price > 0:
        discount_pct = round(
            (actual_price - discounted_price) / actual_price * 100, 1
        )

    discount_amount = None
    if actual_price and discounted_price:
        discount_amount = round(actual_price - discounted_price, 2)

    # ── Rating ───────────────────────────────────────────────────
    rating_tag = soup.find("span", {"data-hook": "rating-out-of-text"}) or \
                 soup.find("i", class_="a-icon-star")
    rating = _clean_number(_safe_text(rating_tag).split(" ")[0])

    rating_count_tag = soup.find("span", {"id": "acrCustomerReviewText"})
    rating_count = _clean_number(_safe_text(rating_count_tag))

    # ── Category ─────────────────────────────────────────────────
    breadcrumbs = soup.select("#wayfinding-breadcrumbs_feature_div li")
    category_parts = [_safe_text(b) for b in breadcrumbs if _safe_text(b)]
    category = " > ".join(category_parts) if category_parts else "Uncategorized"
    category_clean = category_parts[-1] if category_parts else "Uncategorized"

    # ── Brand ─────────────────────────────────────────────────────
    brand = ""
    brand_row = soup.find("tr", {"class": "po-brand"})
    if brand_row:
        brand_td = brand_row.find("td", class_="a-span9")
        brand = _safe_text(brand_td)
    if not brand:
        # Fallback: check "by Brand" link
        by_link = soup.find("a", id="bylineInfo")
        brand = _safe_text(by_link).replace("Brand: ", "").replace("Visit the ", "").replace(" Store", "")

    # ── About Product ─────────────────────────────────────────────
    about_tag = soup.find("div", id="feature-bullets")
    about_product = _safe_text(about_tag)[:1000] if about_tag else ""

    # ── Reviews ──────────────────────────────────────────────────
    review_tag = soup.find("div", {"data-hook": "review"})
    review_title = ""
    review_content = ""
    if review_tag:
        rt = review_tag.find("a", {"data-hook": "review-title"})
        rc = review_tag.find("span", {"data-hook": "review-body"})
        review_title = _safe_text(rt)
        review_content = _safe_text(rc)[:500]

    # ── Images & Links ───────────────────────────────────────────
    img_tag = soup.find("img", id="landingImage") or soup.find("img", id="imgBlkFront")
    img_link = img_tag.get("src", "") if img_tag else ""

    product_link = f"{AMAZON_BASE_URL}/dp/{asin}"

    return {
        "product_id":         asin,
        "product_name":       product_name,
        "category":           category,
        "category_clean":     category_clean,
        "brand":              brand,
        "discounted_price":   discounted_price,
        "actual_price":       actual_price,
        "discount_percentage": discount_pct,
        "discount_amount":    discount_amount,
        "rating":             rating,
        "rating_count":       rating_count,
        "about_product":      about_product,
        "review_title":       review_title,
        "review_content":     review_content,
        "img_link":           img_link,
        "product_link":       product_link,
        "last_updated":       str(date.today()),
    }


def scrape_products_bulk(asins: list[str], delay: bool = True) -> list[dict]:
    """
    Scrape multiple ASINs with a polite delay between each request.

    Args:
        asins:  List of Amazon ASIN strings.
        delay:  If True, sleep between requests (recommended).

    Returns:
        List of product dicts (failed scrapes are skipped).
    """
    results = []
    for i, asin in enumerate(asins, 1):
        log.info(f"[{i}/{len(asins)}] Processing {asin}")
        data = scrape_product(asin)
        if data:
            results.append(data)
        if delay and i < len(asins):
            sleep_for = random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX)
            log.info(f"Sleeping {sleep_for:.1f}s…")
            time.sleep(sleep_for)
    log.info(f"Scraped {len(results)}/{len(asins)} products successfully.")
    return results


# ──────────────────────────────────────────────────────────────────
# Extract ASINs from the existing DB (so we know what to refresh)
# ──────────────────────────────────────────────────────────────────

def get_tracked_asins() -> list[str]:
    """Return all product_ids (ASINs) currently in the DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT product_id FROM products")
        asins = [row[0] for row in cur.fetchall()]
        conn.close()
        return asins
    except Exception as e:
        log.error(f"Could not load ASINs from DB: {e}")
        return []


# ──────────────────────────────────────────────────────────────────
# Quick test (run this file directly to check one product)
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with a popular boAt earphones ASIN (public, no login needed)
    TEST_ASIN = "B07HGGFKDG"
    result = scrape_product(TEST_ASIN)
    if result:
        print("\n✅ Scrape successful!")
        for k, v in result.items():
            print(f"  {k:25s}: {v}")
    else:
        print("❌ Scrape failed — Amazon may have blocked the request. Try again in a minute.")
