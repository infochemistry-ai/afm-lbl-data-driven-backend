from fastapi.testclient import TestClient

from app.main import app


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
