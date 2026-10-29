import os
import tempfile
import pytest

@pytest.fixture()
def client(monkeypatch):
    from ml import storage
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    monkeypatch.setattr(storage, "DB_PATH", tmp.name)
    storage.init_db()
    import app as app_module
    app_module.app.config.update(TESTING=True)
    yield app_module.app.test_client()
    try: os.unlink(tmp.name)
    except OSError: pass

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

def test_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Health overview" in response.data

def test_measurement_saved(client):
    response = client.post("/api/v1/measurements/check", json={
        "heart_rate_bpm": 72, "spo2_percent": 98
    })
    assert response.status_code == 201
    assert response.get_json()["flags"] == []
    assert client.get("/api/v1/measurements").get_json()["items"]

def test_rejects_unknown_field(client):
    response = client.post("/api/v1/measurements/check", json={"mood": 3})
    assert response.status_code == 400

def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"smartcare_http_requests_total" in response.data
