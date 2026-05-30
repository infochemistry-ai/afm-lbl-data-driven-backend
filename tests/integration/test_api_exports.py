from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def _eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


def test_export_lifecycle(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "exp-export"}).json()["id"]
    sid = c.post(f"/api/v1/experiments/{eid}/samples", json={
        "name": "PE11", "layers": [{"position": 1, "polyelectrolyte_id": "PEI"}],
    }).json()["id"]
    with open("tests/fixtures/sample_scan.txt", "rb") as f:
        c.post(f"/api/v1/samples/{sid}/scans", files={"file": ("s.txt", f, "text/plain")})

    r = c.post("/api/v1/exports/dataset", json={"format": "parquet", "filter": {"experiment_id": eid}})
    assert r.status_code == 202
    export_id = r.json()["id"]

    r = c.get(f"/api/v1/exports/{export_id}")
    assert r.json()["status"] == "ready"
    assert r.json()["row_count"] >= 1

    r = c.get(f"/api/v1/exports/{export_id}/download", follow_redirects=False)
    assert r.status_code == 307
