from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExportFilter(BaseModel):
    experiment_id: UUID | None = None
    sample_ids: list[UUID] | None = None
    extractors: list[str] | None = None


class ExportCreate(BaseModel):
    format: Literal["parquet", "csv"] = "parquet"
    filter: ExportFilter = Field(default_factory=ExportFilter)


class ExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    format: str
    filter: dict
    storage_backend: str | None
    storage_key: str | None
    row_count: int | None
    created_at: datetime
    ready_at: datetime | None
    error_message: str | None
