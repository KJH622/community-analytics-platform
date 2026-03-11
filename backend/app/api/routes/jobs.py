from fastapi import APIRouter, HTTPException

from app.jobs.runner import available_jobs, run_job


router = APIRouter()


@router.post("/run/{job_name}")
def run_job_now(job_name: str) -> dict[str, str | int]:
    if job_name not in available_jobs():
        raise HTTPException(status_code=404, detail="Unknown job")
    result = run_job(job_name, triggered_by="api")
    return {
        "job_name": job_name,
        "status": result["status"],
        "items_written": result["items_written"],
    }
