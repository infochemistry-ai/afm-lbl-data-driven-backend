from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.layer import LayerIn, LayerOut


class SampleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    substrate: str = "Si"
    notes: str | None = None
    layers: list[LayerIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _positions_are_contiguous(self) -> "SampleCreate":
        if self.layers:
            positions = sorted(l.position for l in self.layers)
            if positions != list(range(1, len(positions) + 1)):
                raise ValueError("layer positions must be 1..N without gaps or duplicates")
        return self


class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    experiment_id: UUID
    name: str
    substrate: str
    notes: str | None
    created_at: datetime
    layers: list[LayerOut]
