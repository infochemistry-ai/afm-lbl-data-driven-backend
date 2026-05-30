from uuid import uuid4

import pytest

from app.db.models import Experiment, Feature, Layer, Sample
from app.services.ingestion import ingest_scan
from app.workers.celery_app import celery_app
from app.workers.tasks import extract_features_task


@pytest.fixture(autouse=True)
def _eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


def test_running_pipeline_twice_does_not_duplicate_features(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    exp = Experiment(name=f"idem-{uuid4()}")
    sample = Sample(name="PE11", experiment=exp,
                    layers=[Layer(position=1, polyelectrolyte_id="PEI")])
    db_session.add_all([exp, sample])
    db_session.commit()

    with open("tests/fixtures/sample_scan.txt", "rb") as f:
        scan = ingest_scan(db_session, sample_id=sample.id, filename="sample_scan.txt", file=f)
    db_session.commit()

    extract_features_task.run(str(scan.id))
    first_count = db_session.query(Feature).filter(
        (Feature.scan_id == scan.id) | (Feature.sample_id == sample.id)
    ).count()

    extract_features_task.run(str(scan.id))
    second_count = db_session.query(Feature).filter(
        (Feature.scan_id == scan.id) | (Feature.sample_id == sample.id)
    ).count()

    assert first_count > 0
    assert first_count == second_count, "rerunning extractor should upsert, not duplicate"
