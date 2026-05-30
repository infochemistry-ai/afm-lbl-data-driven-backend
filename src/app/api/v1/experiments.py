from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db
from app.db.models import Experiment
from app.schemas.experiment import ExperimentCreate, ExperimentOut

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentOut, status_code=201)
def create(body: ExperimentCreate, session: Session = Depends(db)) -> Experiment:
    exp = Experiment(name=body.name, description=body.description)
    session.add(exp)
    session.flush()
    return exp


@router.get("", response_model=list[ExperimentOut])
def list_(session: Session = Depends(db)) -> list[Experiment]:
    return list(session.scalars(select(Experiment).order_by(Experiment.created_at.desc())))


@router.get("/{experiment_id}", response_model=ExperimentOut)
def get(experiment_id: UUID, session: Session = Depends(db)) -> Experiment:
    exp = session.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(404, "experiment not found")
    return exp
