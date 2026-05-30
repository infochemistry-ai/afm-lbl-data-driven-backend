from fastapi.testclient import TestClient

from app.main import app


def test_create_and_get_experiment(db_session):
    c = TestClient(app)
    r = c.post("/api/v1/experiments", json={"name": "baseline", "description": "first run"})
    assert r.status_code == 201
    eid = r.json()["id"]

    r = c.get(f"/api/v1/experiments/{eid}")
    assert r.status_code == 200
    assert r.json()["name"] == "baseline"

    r = c.get("/api/v1/experiments")
    assert any(e["id"] == eid for e in r.json())
