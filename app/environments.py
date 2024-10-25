import typing as t

from decouple import config


def python_environment():
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower()


def is_testing():
    return python_environment() == "test"


def is_production():
    return python_environment() == "production"


def is_development():
    return python_environment() == "development"
