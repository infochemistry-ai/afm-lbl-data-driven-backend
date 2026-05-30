import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def _eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


def test_full_flow_two_samples(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setenv("EXPORT_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "e2e"}).json()["id"]

    s_bare = c.post(f"/api/v1/experiments/{eid}/samples", json={
        "name": "PE1", "layers": [],
    }).json()["id"]
    s_two = c.post(f"/api/v1/experiments/{eid}/samples", json={
        "name": "PE12",
        "layers": [
            {"position": 1, "polyelectrolyte_id": "PEI"},
            {"position": 2, "polyelectrolyte_id": "PSS"},
        ],
    }).json()["id"]

    with open("tests/fixtures/sample_scan_no_layers.txt", "rb") as f:
        r1 = c.post(f"/api/v1/samples/{s_bare}/scans", files={"file": ("a.txt", f, "text/plain")})
    with open("tests/fixtures/sample_scan_2_layers.txt", "rb") as f:
        r2 = c.post(f"/api/v1/samples/{s_two}/scans", files={"file": ("b.txt", f, "text/plain")})
    assert r1.status_code == r2.status_code == 202

    for r in (r1, r2):
        sid = r.json()["scan_id"]
        assert c.get(f"/api/v1/scans/{sid}").json()["status"] == "ready"

    r_exp = c.post("/api/v1/exports/dataset", json={"format": "csv", "filter": {"experiment_id": eid}})
    assert r_exp.status_code == 202
    export_id = r_exp.json()["id"]

    exp = c.get(f"/api/v1/exports/{export_id}").json()
    assert exp["status"] == "ready"
    assert exp["row_count"] == 2

    # The exported CSV should join scans with their sample's polyelectrolyte_meta columns.
    from app.storage import get_storage as gs
    storage = gs()
    with storage.open(exp["storage_key"]) as fh:
        contents = fh.read().decode("utf-8")
    header = [col.strip('"') for col in contents.splitlines()[0].split(",")]
    assert "polyelectrolyte_meta__n_layers" in header
    assert "iso25178__Sa" in header
    assert "distribution__P95" in header
