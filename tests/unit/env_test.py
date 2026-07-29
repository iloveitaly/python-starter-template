import pytest
from environs import EnvError
from environs.exceptions import EnvValidationError

from app.env import StrictEnv


def test_str_raises_when_env_var_does_not_exist(monkeypatch):
    missing_key = "TEST_MISSING_ENV_DOES_NOT_EXIST"
    monkeypatch.delenv(missing_key, raising=False)

    env = StrictEnv()

    with pytest.raises(EnvError, match=f'Environment variable "{missing_key}" not set'):
        env.str(missing_key)


def test_base_url_accepts_http_origin_with_trailing_slash(monkeypatch):
    key = "TEST_BASE_URL"
    monkeypatch.setenv(key, "https://app.example.com/")

    assert StrictEnv().base_url(key) == "https://app.example.com/"


@pytest.mark.parametrize(
    "value",
    [
        "https://app.example.com",
        "https://app.example.com/path/",
        "https://app.example.com/?q=1",
        "ftp://app.example.com/",
        "http://myhost/",
    ],
)
def test_base_url_rejects_invalid_origins(monkeypatch, value):
    key = "TEST_BASE_URL"
    monkeypatch.setenv(key, value)

    with pytest.raises(EnvValidationError):
        StrictEnv().base_url(key)
