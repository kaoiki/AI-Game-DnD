import pytest

from core.exceptions import AppException


def test_app_exception():
    with pytest.raises(AppException) as exc:
        raise AppException(message="test error", code=4001)

    assert exc.value.message == "test error"
    assert exc.value.code == 4001