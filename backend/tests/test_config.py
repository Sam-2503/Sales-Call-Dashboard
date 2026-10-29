import pytest
from pydantic import ValidationError

from analyser_api.config import Settings


def test_dev_allows_missing_jwt_secret() -> None:
    assert Settings(_env_file=None, environment="dev").jwt_secret is None


@pytest.mark.parametrize("environment", ["test", "prod"])
def test_non_dev_requires_a_long_jwt_secret(environment: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment=environment, jwt_secret=None)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment=environment, jwt_secret="short")
    assert Settings(_env_file=None, environment=environment, jwt_secret="x" * 32)


def test_cors_origins_accept_json_or_comma_separated_values() -> None:
    assert Settings(_env_file=None, cors_origins="https://a.test, https://b.test").cors_origins == [
        "https://a.test",
        "https://b.test",
    ]
    assert Settings(_env_file=None, cors_origins='["https://a.test"]').cors_origins == [
        "https://a.test"
    ]
    assert Settings(_env_file=None, cors_origins="").cors_origins == []


def test_package_settings_are_composed() -> None:
    settings = Settings(_env_file=None)
    assert settings.package.max_audio_minutes == 5
    assert settings.package.min_duration_s == 60
