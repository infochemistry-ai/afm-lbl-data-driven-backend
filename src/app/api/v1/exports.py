from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import db
from app.db.models import Export
from app.schemas.export import ExportCreate, ExportOut
from app.storage import get_storage
from app.workers.tasks import build_export_task

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/dataset", response_model=ExportOut, status_code=202)
def create(body: ExportCreate, session: Session = Depends(db)) -> Export:
    exp = Export(format=body.format, filter=body.filter.model_dump(mode="json", exclude_none=True))
    session.add(exp)
    session.flush()
    session.commit()
    build_export_task.delay(str(exp.id))
    return exp


@router.get("/{export_id}", response_model=ExportOut)
def get(export_id: UUID, session: Session = Depends(db)) -> Export:
    exp = session.get(Export, export_id)
    if exp is None:
        raise HTTPException(404, "export not found")
    return exp


@router.get("/{export_id}/download")
def download(export_id: UUID, session: Session = Depends(db)) -> RedirectResponse:
    exp = session.get(Export, export_id)
    if exp is None or exp.status != "ready" or not exp.storage_key:
        raise HTTPException(404, "export not ready")
    return RedirectResponse(url=get_storage().url(exp.storage_key), status_code=307)
