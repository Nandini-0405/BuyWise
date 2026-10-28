"""
BuyWise - Central Configuration
All paths, settings, and environment variables live here.
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# Base Directories
# ──────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
DB_PATH       = BASE_DIR / "database" / "buywise.db"
DATA_RAW      = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
REPORTS_DIR   = BASE_DIR / "reports"

# ──────────────────────────────────────────────
# Scraper Settings (Free – no API key needed)
# ──────────────────────────────────────────────
SCRAPER_DELAY_MIN = 2   # seconds between requests (be polite)
SCRAPER_DELAY_MAX = 5
SCRAPER_TIMEOUT   = 15  # seconds

# Amazon India base URL
AMAZON_BASE_URL = "https://www.amazon.in"

# User-Agent pool – rotated per request to avoid blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# ──────────────────────────────────────────────
# Email Alerts (Gmail SMTP — free)
# Set these in a .env file or environment variables.
# Never hard-code real credentials here.
# ──────────────────────────────────────────────
ALERT_EMAIL_SENDER   = os.getenv("BUYWISE_EMAIL_SENDER", "")
ALERT_EMAIL_PASSWORD = os.getenv("BUYWISE_EMAIL_PASSWORD", "")   # Gmail App Password
ALERT_EMAIL_HOST     = "smtp.gmail.com"
ALERT_EMAIL_PORT     = 587

# ──────────────────────────────────────────────
# Scheduler Settings
# ──────────────────────────────────────────────
SCHEDULE_HOUR   = 2     # Run daily at 2 AM local time
SCHEDULE_MINUTE = 0

# ──────────────────────────────────────────────
# Scoring Weights (Recommendation Engine)
# ──────────────────────────────────────────────
SCORE_WEIGHT_RATING   = 0.40
SCORE_WEIGHT_DISCOUNT = 0.30
SCORE_WEIGHT_PRICE    = 0.20
SCORE_WEIGHT_REVIEWS  = 0.10
