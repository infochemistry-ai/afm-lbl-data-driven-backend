from pydantic import BaseModel, ConfigDict, Field


class LayerIn(BaseModel):
    position: int = Field(ge=1)
    polyelectrolyte_id: str
    molecular_weight_kda: float | None = None
    concentration_mg_ml: float | None = None
    ph: float | None = None
    salt_concentration_m: float | None = None
    notes: str | None = None


class LayerOut(LayerIn):
    model_config = ConfigDict(from_attributes=True)
