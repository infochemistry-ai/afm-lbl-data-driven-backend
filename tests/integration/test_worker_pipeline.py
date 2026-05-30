from uuid import uuid4

import pytest

from app.db.models import Experiment, Feature, Layer, Sample
from app.services.ingestion import ingest_scan
from app.workers.celery_app import celery_app
from app.workers.tasks import extract_features_task


@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


def test_pipeline_end_to_end(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    exp = Experiment(name=f"e-{uuid4()}")
    sample = Sample(name="PE11", experiment=exp)
    sample.layers = [
        Layer(position=1, polyelectrolyte_id="PEI", molecular_weight_kda=750),
    ]
    db_session.add_all([exp, sample])
    db_session.commit()

    with open("tests/fixtures/sample_scan.txt", "rb") as f:
        scan = ingest_scan(db_session, sample_id=sample.id, filename="sample_scan.txt", file=f)
    db_session.commit()

    result = extract_features_task.run(str(scan.id))
    assert result["status"] == "ready"

    db_session.refresh(scan)
    assert scan.status == "ready"

    features = db_session.query(Feature).filter(
        (Feature.scan_id == scan.id) | (Feature.sample_id == sample.id)
    ).all()
    names = {f.extractor_name for f in features}
    expected = {
        "metadata", "iso25178", "distribution",
        "minmax_patches", "psd_radial", "acf_2d", "acf_rowcol", "tda_persistence",
        "polyelectrolyte_meta", "pe_sequence_kmer", "rdkit_monomer",
    }
    # lacunarity only if the .so is built (it is, locally, and in Docker).
    import app.features.lacunarity as _lac
    if _lac._LIB is not None:
        expected.add("lacunarity")
    assert expected <= names, f"missing: {expected - names}"
