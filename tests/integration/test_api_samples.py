import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workers.celery_app import celery_app


def test_create_sample_with_layers(db_session):
    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "exp1"}).json()["id"]
    body = {
        "name": "PE11",
        "substrate": "Si",
        "layers": [
            {"position": 1, "polyelectrolyte_id": "PEI", "molecular_weight_kda": 750},
            {"position": 2, "polyelectrolyte_id": "PSS", "molecular_weight_kda": 1000},
        ],
    }
    r = c.post(f"/api/v1/experiments/{eid}/samples", json=body)
    assert r.status_code == 201, r.text
    assert len(r.json()["layers"]) == 2


def test_layers_must_be_contiguous(db_session):
    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "exp2"}).json()["id"]
    body = {"name": "X", "layers": [
        {"position": 1, "polyelectrolyte_id": "PEI"},
        {"position": 3, "polyelectrolyte_id": "PSS"},
    ]}
    r = c.post(f"/api/v1/experiments/{eid}/samples", json=body)
    assert r.status_code == 422


def test_unknown_polyelectrolyte(db_session):
    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "exp3"}).json()["id"]
    body = {"name": "Y", "layers": [{"position": 1, "polyelectrolyte_id": "UNKNOWN"}]}
    r = c.post(f"/api/v1/experiments/{eid}/samples", json=body)
    assert r.status_code == 422


@pytest.fixture
def _eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False


def test_sample_features_endpoint(db_session, monkeypatch, tmp_path, _eager):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.storage import get_storage
    get_storage.cache_clear()

    c = TestClient(app)
    eid = c.post("/api/v1/experiments", json={"name": "exp-feat"}).json()["id"]
    sid = c.post(f"/api/v1/experiments/{eid}/samples", json={
        "name": "PE11", "layers": [{"position": 1, "polyelectrolyte_id": "PEI"}],
    }).json()["id"]
    with open("tests/fixtures/sample_scan.txt", "rb") as f:
        c.post(f"/api/v1/samples/{sid}/scans", files={"file": ("s.txt", f, "text/plain")})

    r = c.get(f"/api/v1/samples/{sid}/features")
    assert r.status_code == 200
    names = {g["extractor_name"] for g in r.json()}
    assert "polyelectrolyte_meta" in names
