import pytest

from backend.scripts.provision_test_admin import validate_test_database_target


def valid_test_database_environment() -> dict[str, str]:
    url = "postgresql+psycopg://test-user:test-password@localhost:5435/collab_matcher_test"
    return {
        "DATABASE_URL": url,
        "DATABASE_SYNC_URL": url,
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5435",
        "POSTGRES_DB": "collab_matcher_test",
        "POSTGRES_USER": "test-user",
        "POSTGRES_PASSWORD": "test-password",
    }


def test_test_admin_provisioner_accepts_only_expected_test_database():
    url = validate_test_database_target(valid_test_database_environment())

    assert url.host == "localhost"
    assert url.port == 5435
    assert url.database == "collab_matcher_test"


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("POSTGRES_PORT", "5434"),
        ("POSTGRES_DB", "collab_matcher"),
        (
            "DATABASE_URL",
            "postgresql+psycopg://user:password@localhost:5434/collab_matcher_test",
        ),
        (
            "DATABASE_SYNC_URL",
            "postgresql+psycopg://user:password@localhost:5435/collab_matcher",
        ),
    ),
)
def test_test_admin_provisioner_rejects_normal_database_targets(key, value):
    settings = valid_test_database_environment()
    settings[key] = value

    with pytest.raises(ValueError):
        validate_test_database_target(settings)
