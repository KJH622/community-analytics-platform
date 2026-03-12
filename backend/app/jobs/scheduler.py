from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.ingestion import IngestionService


def build_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    service = IngestionService()

    def _run(job_name: str) -> None:
        with SessionLocal() as db:
            service.run_job(db, job_name)

    scheduler.add_job(lambda: _run("collect_indicators"), CronTrigger(minute="*/30"), id="collect_indicators")
    scheduler.add_job(lambda: _run("collect_news"), CronTrigger(minute="*/20"), id="collect_news")
    scheduler.add_job(lambda: _run("collect_community"), CronTrigger(hour="*/1"), id="collect_community")
    scheduler.add_job(lambda: _run("collect_arca_stock"), CronTrigger(minute=5), id="collect_arca_stock")
    scheduler.add_job(lambda: _run("refresh_snapshots"), CronTrigger(hour=23, minute=55), id="refresh_snapshots")
    return scheduler
