from __future__ import annotations

from typing import Any

from app.db.session import SessionLocal
from app.models.ingestion import IngestionJob
from app.jobs.registry import JOB_REGISTRY


def available_jobs() -> list[str]:
    return sorted(JOB_REGISTRY.keys())


def run_job(job_name: str, triggered_by: str = "scheduler") -> dict[str, Any]:
    if job_name not in JOB_REGISTRY:
        raise KeyError(job_name)
    with SessionLocal() as db:
        job = IngestionJob(job_name=job_name, triggered_by=triggered_by, status="running")
        db.add(job)
        db.commit()
        db.refresh(job)
        try:
            JOB_REGISTRY[job_name](db, job)
            job.status = "success"
            db.commit()
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error_summary = str(exc)
            db.commit()
            raise
        return {
            "job_id": job.id,
            "status": job.status,
            "items_written": job.items_written,
            "items_seen": job.items_seen,
            "items_skipped": job.items_skipped,
        }
