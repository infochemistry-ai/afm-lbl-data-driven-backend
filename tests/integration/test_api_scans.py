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


def test_scan_lifecycle(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "scan-exp"}).json()["id"]
    sid = c.post(f"/api/v1/experiments/{eid}/samples", json={
        "name": "PE11",
        "layers": [{"position": 1, "polyelectrolyte_id": "PEI"}],
    }).json()["id"]

    with open("tests/fixtures/sample_scan.txt", "rb") as f:
        r = c.post(f"/api/v1/samples/{sid}/scans", files={"file": ("sample.txt", f, "text/plain")})
    assert r.status_code == 202, r.text
    scan_id = r.json()["scan_id"]

    # Eager execution means the task already ran by the time POST returned.
    r = c.get(f"/api/v1/scans/{scan_id}")
    assert r.json()["status"] == "ready"

    r = c.get(f"/api/v1/scans/{scan_id}/features")
    names = {g["extractor_name"] for g in r.json()}
    assert {"metadata", "iso25178", "distribution", "polyelectrolyte_meta"} <= names

    r = c.get(f"/api/v1/scans/{scan_id}/raw", follow_redirects=False)
    assert r.status_code == 307
    assert "/api/v1/files/" in r.headers["location"]
