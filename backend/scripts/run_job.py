from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.ingestion import IngestionService


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_job.py <job_name>")
        return 1

    job_name = sys.argv[1]
    Base.metadata.create_all(bind=engine)

    service = IngestionService()
    with SessionLocal() as db:
        status, message, records = service.run_job(db, job_name)

    print(f"job={job_name}")
    print(f"status={status.value}")
    print(f"records_processed={records}")
    print(message)
    return 0 if status.value == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
