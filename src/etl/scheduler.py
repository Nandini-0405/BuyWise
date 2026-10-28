"""
BuyWise - Daily Scheduler
Runs the full pipeline automatically every day at 2 AM.
Uses APScheduler — free, runs locally.

Start it once and leave it running in the background:
    python src/etl/scheduler.py
"""

import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SCHEDULE_HOUR, SCHEDULE_MINUTE
from etl.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("buywise.scheduler")


def scheduled_job():
    log.info("⏰ Scheduled run triggered.")
    run_pipeline()


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE),
        id="daily_refresh",
        name="BuyWise Daily Amazon Refresh",
        replace_existing=True,
    )

    log.info(f"✅ Scheduler started. Pipeline will run every day at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} IST.")
    log.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
