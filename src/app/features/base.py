"""
Protocol and shared data types for feature extractors.

A :class:`FeatureExtractor` consumes a preprocessed :class:`~app.parsers.base.Surface`
together with an :class:`ExtractionContext` (carrying the sample's LbL recipe
and the catalog of polyelectrolytes) and returns a flat ``dict`` of named
scalar / list values that the worker stores as one row in the ``features``
table. Each extractor declares its ``name``, semantic ``version``, ``scope``
(``"scan"`` or ``"sample"``) and ``default_params`` as class attributes.

:func:`params_hash` produces a stable hash of any params dict; it is part of
the uniqueness key of stored feature rows, which allows the same extractor
to coexist in multiple parameter-tuned variants without collision.
"""

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
    monomer_smiles: str = ""


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
