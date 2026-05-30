from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db
from app.config import get_settings
from app.storage import get_storage

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz(session: Session = Depends(db)) -> dict:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/readyz")
def readyz(session: Session = Depends(db)) -> dict:
    session.execute(text("SELECT 1"))
    s = get_storage()
    return {"status": "ok", "storage": s.backend_name, "env": get_settings().app_env}
