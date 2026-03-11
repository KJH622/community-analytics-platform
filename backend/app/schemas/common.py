from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int


class PaginatedResponse(BaseModel):
    items: list[Any]
    meta: PaginationMeta


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp: datetime


class DateRangeParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
