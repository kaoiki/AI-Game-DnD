from core.response import success, error
import pytest

pytestmark = pytest.mark.skip(reason="旧阶段测试，暂不参与当前阶段回归")


def test_success_response():
    res = success(data={"name": "test"}).model_dump()

    assert res["code"] == 0
    assert res["message"] == "success"
    assert res["data"]["name"] == "test"


def test_error_response():
    res = error(message="bad request", code=400).model_dump()

    assert res["code"] == 400
    assert res["message"] == "bad request"
    assert res["data"] is None