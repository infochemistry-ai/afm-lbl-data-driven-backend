from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db
from app.schemas.polyelectrolyte import PolyelectrolyteOut
from app.services.polyelectrolytes import get_all

router = APIRouter(prefix="/polyelectrolytes", tags=["polyelectrolytes"])


@router.get("", response_model=list[PolyelectrolyteOut])
def list_polyelectrolytes(session: Session = Depends(db)) -> list:
    return get_all(session)
