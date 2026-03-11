from pydantic import BaseModel


class JobRunResponse(BaseModel):
    job_name: str
    status: str
    message: str
    records_processed: int = 0
