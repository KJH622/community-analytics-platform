from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.jobs import JobRunResponse
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
service = IngestionService()


@router.post("/run/{job_name}", response_model=JobRunResponse)
def run_job(job_name: str, db: Session = Depends(get_db)):
    status, message, records = service.run_job(db, job_name)
    return JobRunResponse(
        job_name=job_name,
        status=status.value,
        message=message,
        records_processed=records,
    )
