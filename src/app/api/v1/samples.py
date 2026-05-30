from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db
from app.db.models import Experiment, Feature, Layer, Polyelectrolyte, Sample
from app.schemas.feature import FeatureGroupOut
from app.schemas.sample import SampleCreate, SampleOut

router = APIRouter(tags=["samples"])


@router.post("/experiments/{experiment_id}/samples", response_model=SampleOut, status_code=201)
def create(experiment_id: UUID, body: SampleCreate, session: Session = Depends(db)) -> Sample:
    if session.get(Experiment, experiment_id) is None:
        raise HTTPException(404, "experiment not found")
    catalog_ids = {p for p in session.scalars(select(Polyelectrolyte.id))}
    for l in body.layers:
        if l.polyelectrolyte_id not in catalog_ids:
            raise HTTPException(422, f"unknown polyelectrolyte_id: {l.polyelectrolyte_id}")

    sample = Sample(
        experiment_id=experiment_id, name=body.name, substrate=body.substrate, notes=body.notes,
        layers=[Layer(**l.model_dump()) for l in body.layers],
    )
    session.add(sample)
    try:
        session.flush()
    except Exception as e:
        raise HTTPException(409, f"sample creation failed: {e}") from e
    return sample


@router.get("/samples", response_model=list[SampleOut])
def list_(experiment_id: UUID | None = Query(default=None), session: Session = Depends(db)) -> list[Sample]:
    stmt = select(Sample)
    if experiment_id is not None:
        stmt = stmt.where(Sample.experiment_id == experiment_id)
    return list(session.scalars(stmt.order_by(Sample.created_at.desc())))


@router.get("/samples/{sample_id}", response_model=SampleOut)
def get(sample_id: UUID, session: Session = Depends(db)) -> Sample:
    sample = session.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(404, "sample not found")
    return sample


@router.get("/samples/{sample_id}/features", response_model=list[FeatureGroupOut])
def list_features(
    sample_id: UUID,
    extractor: str | None = None,
    version: str | None = None,
    session: Session = Depends(db),
) -> list[Feature]:
    if session.get(Sample, sample_id) is None:
        raise HTTPException(404, "sample not found")
    from sqlalchemy import select
    stmt = select(Feature).where(Feature.sample_id == sample_id)
    if extractor:
        stmt = stmt.where(Feature.extractor_name == extractor)
    if version:
        stmt = stmt.where(Feature.extractor_version == version)
    rows = list(session.scalars(stmt))
    if version is None:
        latest: dict[tuple, Feature] = {}
        for r in rows:
            key = (r.extractor_name, r.params_hash)
            if key not in latest or r.computed_at > latest[key].computed_at:
                latest[key] = r
        rows = list(latest.values())
    return rows
