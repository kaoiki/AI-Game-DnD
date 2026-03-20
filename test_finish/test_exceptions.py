import pytest

from core.exceptions import AppException
import pytest

pytestmark = pytest.mark.skip(reason="旧阶段测试，暂不参与当前阶段回归")


def test_app_exception():
    with pytest.raises(AppException) as exc:
        raise AppException(message="test error", code=4001)

    assert exc.value.message == "test error"
    assert exc.value.code == 4001