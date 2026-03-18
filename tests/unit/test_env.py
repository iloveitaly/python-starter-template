import pytest
from environs import EnvError

from app.env import StrictEnv


def test_str_raises_when_env_var_does_not_exist(monkeypatch):
    missing_key = "COPILOT_TEST_MISSING_ENV_DOES_NOT_EXIST_12345"
    monkeypatch.delenv(missing_key, raising=False)

    env = StrictEnv()

    with pytest.raises(EnvError, match=f'Environment variable "{missing_key}" not set'):
        env.str(missing_key)
