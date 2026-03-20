from fastapi.testclient import TestClient

from main import app
import pytest

pytestmark = pytest.mark.skip(reason="旧阶段测试，暂不参与当前阶段回归")

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["code"] == 0
    assert data["message"] == "success"
    assert data["data"]["status"] == "ok"