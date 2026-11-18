import pytest

from backend.app.core.config import Settings


def test_production_settings_reject_default_jwt_secret():
    with pytest.raises(ValueError, match="explicitly configured SECRET_KEY"):
        Settings(ENVIRONMENT="production", _env_file=None)


def test_production_settings_reject_short_jwt_secret():
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(ENVIRONMENT="production", SECRET_KEY="too-short", _env_file=None)


def test_production_settings_accept_explicit_long_jwt_secret():
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-test-only-secret-of-at-least-32-characters",
        _env_file=None,
    )
    assert settings.SECRET_KEY == "a-test-only-secret-of-at-least-32-characters"
