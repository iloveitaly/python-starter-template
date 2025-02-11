import typing as t

from decouple import config


def python_environment():
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower()


def is_testing():
    return python_environment() == "test"


def is_production():
    return python_environment() == "production"


def is_staging():
    return python_environment() == "staging"


def is_development():
    return python_environment() == "development"


def is_job_monitor():
    "is this the production flower application"
    # TODO should use a ENV var for app name, rather than hardcoding; how we determine & store container names needs to be refactored
    return config("CONTAINER_APP_NAME", default="", cast=str) == "prod-jmon"
