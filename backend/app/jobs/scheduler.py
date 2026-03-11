from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.jobs.runner import run_job


logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone=get_settings().default_timezone)


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(run_job, "interval", hours=6, args=["collect_indicators"], id="collect_indicators")
    scheduler.add_job(run_job, "interval", minutes=30, args=["collect_news"], id="collect_news")
    scheduler.add_job(
        run_job, "interval", hours=1, args=["collect_mock_community"], id="collect_mock_community"
    )
    scheduler.add_job(
        run_job, "cron", hour=0, minute=10, args=["compute_daily_snapshots"], id="daily_snapshot"
    )
    scheduler.add_job(
        run_job, "interval", hours=6, args=["collect_political_indicators"], id="collect_political_indicators"
    )
    scheduler.add_job(
        run_job, "interval", hours=2, args=["collect_political_posts"], id="collect_political_posts"
    )
    scheduler.add_job(
        run_job,
        "cron",
        hour=0,
        minute=20,
        args=["compute_political_daily_snapshots"],
        id="political_daily_snapshot",
    )
    scheduler.start()
    logger.info("Scheduler started with %s jobs", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
