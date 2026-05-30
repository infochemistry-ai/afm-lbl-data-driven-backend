import hashlib
import json
from typing import ClassVar, Literal, Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.parsers.base import Surface


class LayerView(BaseModel):
    model_config = ConfigDict(frozen=True)
    position: int
    polyelectrolyte_id: str
    molecular_weight_kda: float | None = None
    concentration_mg_ml: float | None = None
    ph: float | None = None
    salt_concentration_m: float | None = None


class PolyelectrolyteView(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    charge_sign: int
    charge_group: str
    is_strong: bool
    pka: float | None
    monomer_mw_g_mol: float
    backbone_type: str


class ScanMetaView(BaseModel):
    model_config = ConfigDict(frozen=True)
    pixels_x: int
    pixels_y: int
    width_um: float | None
    height_um: float | None
    units: str | None


class ExtractionContext(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    sample_id: UUID
    scan_id: UUID | None
    layers: list[LayerView]
    polyelectrolytes: dict[str, PolyelectrolyteView]
    scan_meta: ScanMetaView | None


FeatureValue = float | int | str | None
Scope = Literal["scan", "sample"]


@runtime_checkable
class FeatureExtractor(Protocol):
    name: ClassVar[str]
    version: ClassVar[str]
    scope: ClassVar[Scope]
    default_params: ClassVar[dict]

    def extract(
        self,
        surface: Surface | None,
        ctx: ExtractionContext,
        params: dict,
    ) -> dict[str, FeatureValue]: ...


def params_hash(params: dict) -> str:
    payload = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
