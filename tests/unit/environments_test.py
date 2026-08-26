import pytest
from environs import EnvError
from environs.exceptions import EnvValidationError

from app.environments import (
    PythonEnvironment,
    assert_environment,
    is_development,
    is_preview,
    is_production,
    is_productionish,
    is_staging,
    is_testing,
    python_environment,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("development", PythonEnvironment.DEVELOPMENT),
        ("TEST", PythonEnvironment.TEST),
        ("production", PythonEnvironment.PRODUCTION),
        ("staging", PythonEnvironment.STAGING),
        ("preview", PythonEnvironment.PREVIEW),
    ],
)
def test_python_environment_parses_known_values(monkeypatch, value, expected):
    monkeypatch.setenv("PYTHON_ENV", value)

    current = python_environment()

    assert current is expected
    # StrEnum remains a str so log/Sentry/path interpolation keep working
    assert current == value.lower()


def test_python_environment_defaults_to_development(monkeypatch):
    monkeypatch.delenv("PYTHON_ENV", raising=False)

    assert python_environment() is PythonEnvironment.DEVELOPMENT
    assert is_development()


def test_python_environment_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "sandbox")

    with pytest.raises(ValueError, match="'sandbox' is not a valid PythonEnvironment"):
        python_environment()


def test_assert_environment_returns_parsed_value(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "TEST")

    assert assert_environment() is PythonEnvironment.TEST


def test_assert_environment_requires_python_env(monkeypatch):
    monkeypatch.delenv("PYTHON_ENV", raising=False)

    with pytest.raises(EnvError, match='Environment variable "PYTHON_ENV" not set'):
        assert_environment()


@pytest.mark.parametrize("value", ["", "   "])
def test_assert_environment_rejects_empty_python_env(monkeypatch, value):
    monkeypatch.setenv("PYTHON_ENV", value)

    with pytest.raises(EnvValidationError, match="PYTHON_ENV must not be empty"):
        assert_environment()


def test_assert_environment_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "sandbox")

    with pytest.raises(ValueError, match="'sandbox' is not a valid PythonEnvironment"):
        assert_environment()


@pytest.mark.parametrize(
    (
        "value",
        "development",
        "testing",
        "production",
        "staging",
        "preview",
        "productionish",
    ),
    [
        ("development", True, False, False, False, False, False),
        ("test", False, True, False, False, False, False),
        ("production", False, False, True, False, False, True),
        ("staging", False, False, False, True, False, True),
        ("preview", False, False, False, False, True, True),
    ],
)
def test_environment_predicates(
    monkeypatch,
    value,
    development,
    testing,
    production,
    staging,
    preview,
    productionish,
):
    monkeypatch.setenv("PYTHON_ENV", value)

    assert is_development() is development
    assert is_testing() is testing
    assert is_production() is production
    assert is_staging() is staging
    assert is_preview() is preview
    assert is_productionish() is productionish
