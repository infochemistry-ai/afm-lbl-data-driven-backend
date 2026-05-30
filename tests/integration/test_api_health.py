from fastapi.testclient import TestClient

from app.main import app


def test_healthz(db_session):
    client = TestClient(app)
    r = client.get("/api/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_polyelectrolytes(db_session):
    client = TestClient(app)
    r = client.get("/api/v1/polyelectrolytes")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert "PEI" in ids and "PSS" in ids
