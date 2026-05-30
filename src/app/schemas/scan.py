from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sample_id: UUID
    original_filename: str
    parser_name: str
    channel: str | None
    width_um: float | None
    height_um: float | None
    pixels_x: int | None
    pixels_y: int | None
    units: str | None
    status: str
    error_message: dict | None
    uploaded_at: datetime
    processed_at: datetime | None


class ScanAcceptedOut(BaseModel):
    scan_id: UUID
    status: str
    status_url: str


class RecomputeIn(BaseModel):
    extractors: list[str] | None = None
