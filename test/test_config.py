from core.config import settings


def test_config_loaded():
    assert settings.app_name is not None
    assert settings.app_version is not None
    assert isinstance(settings.port, int)