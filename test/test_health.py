from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["code"] == 0
    assert data["message"] == "success"
    assert data["data"]["status"] == "ok"