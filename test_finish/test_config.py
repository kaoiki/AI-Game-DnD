from core.config import settings
import pytest

pytestmark = pytest.mark.skip(reason="旧阶段测试，暂不参与当前阶段回归")


def test_config_loaded():
    assert settings.app_name is not None
    assert settings.app_version is not None
    assert isinstance(settings.port, int)