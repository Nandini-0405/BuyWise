"""
BuyWise - Daily Pipeline Orchestrator
Runs the full: scrape → clean → save → check alerts cycle.
"""

import logging
import smtplib
import sqlite3
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    DB_PATH,
    ALERT_EMAIL_HOST,
    ALERT_EMAIL_PORT,
    ALERT_EMAIL_SENDER,
    ALERT_EMAIL_PASSWORD,
)
from etl.amazon_scraper import scrape_products_bulk, get_tracked_asins
from etl.load_database import init_db, save_products

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("reports/pipeline.log", mode="a"),
    ]
)
log = logging.getLogger("buywise.pipeline")


# ──────────────────────────────────────────────────────────────────
# Wishlist Alert Checker
# ──────────────────────────────────────────────────────────────────

def _send_email(to: str, product_name: str, current_price: float, target: float, link: str):
    subject = f"🎉 BuyWise: Price Drop on {product_name[:40]}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;">
    <h2>🎯 Your target price was reached!</h2>
    <p><b>{product_name}</b></p>
    <p>Current Price: <b style="color:#10b981;">₹{current_price:,.0f}</b></p>
    <p>Your Target:  <b style="color:#6366f1;">₹{target:,.0f}</b></p>
    <a href="{link}" style="background:#6366f1;color:white;padding:10px 20px;
       border-radius:6px;text-decoration:none;font-weight:bold;">Buy Now on Amazon →</a>
    <p style="color:#9ca3af;font-size:0.8rem;margin-top:20px;">Sent by BuyWise</p>
    </body></html>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = ALERT_EMAIL_SENDER
        msg["To"] = to
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP(ALERT_EMAIL_HOST, ALERT_EMAIL_PORT) as s:
            s.ehlo()
            s.starttls()
            s.login(ALERT_EMAIL_SENDER, ALERT_EMAIL_PASSWORD)
            s.sendmail(ALERT_EMAIL_SENDER, to, msg.as_string())
        log.info(f"✅ Alert email sent to {to} for {product_name[:30]}")
    except Exception as e:
        log.error(f"Email failed: {e}")


def check_wishlist_alerts():
    """Check all wishlist items and email if target price is met."""
    if not (ALERT_EMAIL_SENDER and ALERT_EMAIL_PASSWORD):
        log.info("Email not configured — skipping alert check.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT w.id, w.product_id, p.product_name, p.discounted_price,
                   p.product_link, w.target_price, w.alert_sent
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            WHERE p.discounted_price <= w.target_price AND w.alert_sent = 0
        """).fetchall()

        for row in rows:
            wid, pid, name, price, link, target, _ = row
            log.info(f"🎯 Target met for {name[:40]} — ₹{price} ≤ ₹{target}")
            _send_email(ALERT_EMAIL_SENDER, name, price, target, link)
            conn.execute("UPDATE wishlist SET alert_sent=1 WHERE id=?", (wid,))

        conn.commit()
        conn.close()
        log.info(f"Alert check complete. {len(rows)} alert(s) sent.")
    except Exception as e:
        log.error(f"Wishlist alert check failed: {e}")


# ──────────────────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────────────────

def run_pipeline(extra_asins: list[str] | None = None):
    log.info("=" * 60)
    log.info("BuyWise Daily Pipeline — START")
    log.info("=" * 60)

    # Step 1 — Init DB
    init_db()

    # Step 2 — Get existing ASINs + wishlist ASINs
    tracked = get_tracked_asins()

    wishlist_asins = []
    try:
        conn = sqlite3.connect(DB_PATH)
        wishlist_asins = [r[0] for r in conn.execute("SELECT product_id FROM wishlist").fetchall()]
        conn.close()
    except Exception:
        pass

    all_asins = list(set(tracked + wishlist_asins + (extra_asins or [])))
    log.info(f"Total ASINs to refresh: {len(all_asins)}")

    if not all_asins:
        log.warning("No ASINs tracked yet. Add products via the dashboard Wishlist or run:")
        log.warning("  python src/etl/pipeline.py B08L5TNJCE")
        return

    # Step 3 — Scrape
    products = scrape_products_bulk(all_asins, delay=True)

    # Step 4 — Save
    save_products(products)

    # Step 5 — Check price alerts
    check_wishlist_alerts()

    log.info("=" * 60)
    log.info("BuyWise Daily Pipeline — DONE")
    log.info("=" * 60)


if __name__ == "__main__":
    extras = sys.argv[1:] if len(sys.argv) > 1 else []
    run_pipeline(extra_asins=extras)
