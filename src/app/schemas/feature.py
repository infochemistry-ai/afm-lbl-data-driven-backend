from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FeatureGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    extractor_name: str
    extractor_version: str
    extractor_scope: str
    params: dict
    values: dict[str, Any]
    computed_at: datetime
    scan_id: UUID | None
    sample_id: UUID | None
