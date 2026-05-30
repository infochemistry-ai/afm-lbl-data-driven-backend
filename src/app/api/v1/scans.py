from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db
from app.db.models import Sample, Scan, Feature
from app.schemas.feature import FeatureGroupOut
from app.schemas.scan import ScanAcceptedOut, ScanOut, RecomputeIn
from app.services.ingestion import ingest_scan
from app.storage import get_storage
from app.workers.tasks import extract_features_task

router = APIRouter(tags=["scans"])


@router.post("/samples/{sample_id}/scans", response_model=ScanAcceptedOut, status_code=202)
def upload(
    sample_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    parser_hint: str | None = Form(default=None),
    channel_hint: str | None = Form(default=None),
    session: Session = Depends(db),
) -> ScanAcceptedOut:
    sample = session.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(404, "sample not found")
    try:
        scan = ingest_scan(
            session, sample_id=sample_id, filename=file.filename or "upload.bin",
            file=file.file, parser_hint=parser_hint, channel_hint=channel_hint,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    session.commit()
    extract_features_task.delay(str(scan.id))
    return ScanAcceptedOut(
        scan_id=scan.id, status=scan.status,
        status_url=str(request.url_for("get_scan", scan_id=scan.id)),
    )


@router.get("/samples/{sample_id}/scans", response_model=list[ScanOut])
def list_for_sample(sample_id: UUID, session: Session = Depends(db)) -> list[Scan]:
    return list(session.scalars(select(Scan).where(Scan.sample_id == sample_id).order_by(Scan.uploaded_at.desc())))


@router.get("/scans/{scan_id}", response_model=ScanOut, name="get_scan")
def get_scan(scan_id: UUID, session: Session = Depends(db)) -> Scan:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    return scan


@router.get("/scans/{scan_id}/raw")
def get_raw(scan_id: UUID, session: Session = Depends(db)) -> RedirectResponse:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    return RedirectResponse(url=get_storage().url(scan.storage_key), status_code=307)


@router.get("/scans/{scan_id}/features", response_model=list[FeatureGroupOut])
def get_features(
    scan_id: UUID,
    extractor: str | None = None,
    version: str | None = None,
    session: Session = Depends(db),
) -> list[Feature]:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    stmt = select(Feature).where(
        (Feature.scan_id == scan_id) | (Feature.sample_id == scan.sample_id)
    )
    if extractor:
        stmt = stmt.where(Feature.extractor_name == extractor)
    if version:
        stmt = stmt.where(Feature.extractor_version == version)
    rows = list(session.scalars(stmt))
    if version is None:
        latest: dict[tuple, Feature] = {}
        for r in rows:
            key = (r.extractor_name, r.extractor_scope, r.params_hash)
            if key not in latest or r.computed_at > latest[key].computed_at:
                latest[key] = r
        rows = list(latest.values())
    return rows


@router.post("/scans/{scan_id}/recompute", response_model=ScanAcceptedOut, status_code=202)
def recompute(scan_id: UUID, request: Request, body: RecomputeIn | None = None, session: Session = Depends(db)) -> ScanAcceptedOut:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    only = body.extractors if body else None
    extract_features_task.delay(str(scan.id), only=only)
    return ScanAcceptedOut(
        scan_id=scan.id, status="pending",
        status_url=str(request.url_for("get_scan", scan_id=scan.id)),
    )


@router.post("/samples/{sample_id}/recompute", status_code=202)
def recompute_sample(sample_id: UUID, body: RecomputeIn | None = None, session: Session = Depends(db)) -> dict:
    scans = list(session.scalars(select(Scan).where(Scan.sample_id == sample_id)))
    only = body.extractors if body else None
    for s in scans:
        extract_features_task.delay(str(s.id), only=only)
    return {"enqueued": len(scans)}
