"""
Feature-extraction pipeline driver.

:func:`run_pipeline` is invoked by the Celery worker for each scan; it:
  1. retrieves the raw AFM file from the configured storage backend,
  2. parses it through the registered parser,
  3. applies the standardised preprocessing chain,
  4. iterates every registered scan-scope extractor on the cleaned surface,
  5. iterates every registered sample-scope extractor on the recipe context,
  6. upserts each result into the ``features`` table keyed by
     ``(scope id, extractor_name, extractor_version, params_hash)``.

An individual extractor failure is caught and recorded in
``scan.error_message`` without aborting the remaining work — partial feature
coverage is preferred over losing every result of a long-running pipeline.
"""

import os
import shutil
import tempfile
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Feature, Layer, Polyelectrolyte, Sample, Scan
from app.features import all_extractors_by_scope
from app.features.base import (
    ExtractionContext,
    LayerView,
    PolyelectrolyteView,
    ScanMetaView,
    params_hash,
)
from app.features.preprocessing import preprocess
from app.logging import get_logger
from app.parsers import get_parser_by_name
from app.storage import get_storage

log = get_logger(__name__)


def build_context(session: Session, scan: Scan) -> ExtractionContext:
    layers_rows = list(
        session.scalars(
            select(Layer).where(Layer.sample_id == scan.sample_id).order_by(Layer.position)
        )
    )
    catalog_ids = {l.polyelectrolyte_id for l in layers_rows}
    pe_rows = list(
        session.scalars(select(Polyelectrolyte).where(Polyelectrolyte.id.in_(catalog_ids)))
    )
    return ExtractionContext(
        sample_id=scan.sample_id,
        scan_id=scan.id,
        layers=[
            LayerView(
                position=l.position,
                polyelectrolyte_id=l.polyelectrolyte_id,
                molecular_weight_kda=l.molecular_weight_kda,
                concentration_mg_ml=l.concentration_mg_ml,
                ph=l.ph,
                salt_concentration_m=l.salt_concentration_m,
            )
            for l in layers_rows
        ],
        polyelectrolytes={
            pe.id: PolyelectrolyteView(
                id=pe.id,
                charge_sign=pe.charge_sign,
                charge_group=pe.charge_group,
                is_strong=pe.is_strong,
                pka=pe.pka,
                monomer_mw_g_mol=pe.monomer_mw_g_mol,
                backbone_type=pe.backbone_type,
                monomer_smiles=pe.monomer_smiles,
            )
            for pe in pe_rows
        },
        scan_meta=ScanMetaView(
            pixels_x=scan.pixels_x or 0,
            pixels_y=scan.pixels_y or 0,
            width_um=scan.width_um,
            height_um=scan.height_um,
            units=scan.units,
        ),
    )


def _upsert_feature(
    session: Session,
    *,
    scan_id: UUID | None,
    sample_id: UUID | None,
    name: str,
    version: str,
    scope: str,
    params: dict,
    values: dict,
) -> None:
    p_hash = params_hash(params)
    payload = dict(
        scan_id=scan_id,
        sample_id=sample_id,
        extractor_name=name,
        extractor_version=version,
        extractor_scope=scope,
        params_hash=p_hash,
        params=params,
        values=values,
        computed_at=datetime.now(timezone.utc),
    )
    stmt = insert(Feature).values(payload)
    if scan_id is not None:
        stmt = stmt.on_conflict_do_update(
            index_elements=["scan_id", "extractor_name", "extractor_version", "params_hash"],
            index_where=text("scan_id IS NOT NULL"),
            set_={
                "values": payload["values"],
                "computed_at": payload["computed_at"],
                "params": payload["params"],
            },
        )
    else:
        stmt = stmt.on_conflict_do_update(
            index_elements=["sample_id", "extractor_name", "extractor_version", "params_hash"],
            index_where=text("sample_id IS NOT NULL"),
            set_={
                "values": payload["values"],
                "computed_at": payload["computed_at"],
                "params": payload["params"],
            },
        )
    session.execute(stmt)


def run_pipeline(
    session: Session, scan: Scan, *, only: list[str] | None = None
) -> dict[str, str]:
    """Returns mapping of extractor_name -> error string for any failed extractors."""
    storage = get_storage()
    parser_cls = get_parser_by_name(scan.parser_name)
    parser = parser_cls()

    suffix = "." + scan.original_filename.rsplit(".", 1)[-1]
    with storage.open(scan.storage_key) as fh:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            shutil.copyfileobj(fh, tmp)
            tmp_path = tmp.name

    try:
        surface = parser.parse(tmp_path)
        cleaned, preprocessing_steps = preprocess(surface)

        ctx = build_context(session, scan)
        errors: dict[str, str] = {}

        scan_extractors = all_extractors_by_scope("scan")
        if only is not None:
            scan_extractors = [c for c in scan_extractors if c.name in only]
        for cls in scan_extractors:
            try:
                values = cls().extract(cleaned, ctx, cls.default_params)
                if cls.name == "metadata":
                    values["preprocessing_steps"] = preprocessing_steps
                _upsert_feature(
                    session,
                    scan_id=scan.id,
                    sample_id=None,
                    name=cls.name,
                    version=cls.version,
                    scope="scan",
                    params=cls.default_params,
                    values=values,
                )
            except Exception as e:
                errors[cls.name] = repr(e)
                log.exception("scan_extractor_failed", extractor=cls.name, scan_id=str(scan.id))

        sample_extractors = all_extractors_by_scope("sample")
        if only is not None:
            sample_extractors = [c for c in sample_extractors if c.name in only]
        for cls in sample_extractors:
            try:
                values = cls().extract(None, ctx, cls.default_params)
                _upsert_feature(
                    session,
                    scan_id=None,
                    sample_id=scan.sample_id,
                    name=cls.name,
                    version=cls.version,
                    scope="sample",
                    params=cls.default_params,
                    values=values,
                )
            except Exception as e:
                errors[cls.name] = repr(e)
                log.exception(
                    "sample_extractor_failed", extractor=cls.name, sample_id=str(scan.sample_id)
                )

        session.commit()
        return errors
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
