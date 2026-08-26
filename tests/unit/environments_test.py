import pytest

from app.environments import (
    PythonEnvironment,
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

    assert python_environment() is expected


def test_python_environment_defaults_to_development(monkeypatch):
    monkeypatch.delenv("PYTHON_ENV", raising=False)

    assert python_environment() is PythonEnvironment.DEVELOPMENT
    assert is_development()


def test_python_environment_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("PYTHON_ENV", "sandbox")

    with pytest.raises(ValueError, match="'sandbox' is not a valid PythonEnvironment"):
        python_environment()


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
