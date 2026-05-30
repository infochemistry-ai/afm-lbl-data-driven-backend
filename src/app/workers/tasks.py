from datetime import datetime, timezone

from app.db.models import Scan
from app.db.session import get_session_factory
from app.logging import get_logger
from app.services.features import run_pipeline
from app.workers.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=10)
def extract_features_task(self, scan_id: str, only: list[str] | None = None) -> dict:
    Session = get_session_factory()
    with Session() as session:
        scan = session.get(Scan, scan_id)
        if scan is None:
            return {"status": "missing"}
        scan.status = "processing"
        session.commit()
        try:
            errors = run_pipeline(session, scan, only=only)
            scan.status = "ready"
            scan.error_message = errors or None
            scan.processed_at = datetime.now(timezone.utc)
            session.commit()
            return {"status": "ready", "errors": errors}
        except Exception as e:
            log.exception("pipeline_failed", scan_id=scan_id)
            scan.status = "failed"
            scan.error_message = {"__pipeline__": repr(e)}
            session.commit()
            raise


from app.db.models import Export  # noqa: E402
from app.services.dataset import build_dataset  # noqa: E402


@celery_app.task(bind=True, max_retries=1)
def build_export_task(self, export_id: str) -> dict:
    Session = get_session_factory()
    with Session() as session:
        exp = session.get(Export, export_id)
        if exp is None:
            return {"status": "missing"}
        exp.status = "processing"
        session.commit()
        try:
            from app.storage import get_storage
            key, row_count = build_dataset(session, filter_=exp.filter, format_=exp.format, export_id=exp.id)
            exp.status = "ready"
            exp.storage_backend = get_storage().backend_name
            exp.storage_key = key
            exp.row_count = row_count
            exp.ready_at = datetime.now(timezone.utc)
            session.commit()
            return {"status": "ready", "row_count": row_count}
        except Exception as e:
            log.exception("export_failed", export_id=export_id)
            exp.status = "failed"
            exp.error_message = repr(e)
            session.commit()
            raise
