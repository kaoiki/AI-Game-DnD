from fastapi.testclient import TestClient

from  main import app
import pytest

pytestmark = pytest.mark.skip(reason="旧阶段测试，暂不参与当前阶段回归")


client = TestClient(app)


def test_invoke_init_success():
    response = client.post(
        "/invoke",
        json={
            "event": {
                "type": "init"
            }
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert body["data"]["event"]["type"] == "init"
    assert body["data"]["payload"]["message"] == "mock init handled"


def test_invoke_invalid_event_type():
    response = client.post(
        "/invoke",
        json={
            "event": {
                "type": "abc"
            }
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert body["code"] == 422
    assert body["message"] == "validation error"
    assert isinstance(body["data"], list)
    assert body["data"][0]["loc"] == ["body", "event", "type"]


def test_invoke_unregistered_event_type():
    response = client.post(
        "/invoke",
        json={
            "event": {
                "type": "decision"
            }
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 1
    assert "No handler registered" in body["message"]
    assert body["data"] is None