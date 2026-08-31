import os

import pytest

from tests.concurrent_tests import (
    REDIS_DB_OFFSET,
    configure_xdist_worker_environment,
    replace_url_path,
    worker_database_name,
    worker_index,
)


def test_worker_index_parses_gateway_id():
    assert worker_index("gw0") == 0
    assert worker_index("gw12") == 12


def test_worker_index_rejects_unexpected_ids():
    with pytest.raises(AssertionError, match="unexpected pytest-xdist worker id"):
        worker_index("master")


def test_worker_database_name():
    assert worker_database_name(0) == "test_xdist_0"
    assert worker_database_name(7) == "test_xdist_7"


def test_replace_url_path_rewrites_postgres_and_redis():
    assert (
        replace_url_path(
            "postgresql://root:password@localhost:5432/test", "test_xdist_3"
        )
        == "postgresql://root:password@localhost:5432/test_xdist_3"
    )
    assert (
        replace_url_path("redis://localhost:6379/2", "5") == "redis://localhost:6379/5"
    )


def test_configure_xdist_worker_environment_is_noop_without_worker(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.setenv(
        "TEST_DATABASE_URL", "postgresql://root:password@localhost:5432/test"
    )
    monkeypatch.setenv("TEST_REDIS_URL", "redis://localhost:6379/2")

    configure_xdist_worker_environment()

    assert (
        os.environ["TEST_DATABASE_URL"]
        == "postgresql://root:password@localhost:5432/test"
    )
    assert os.environ["TEST_REDIS_URL"] == "redis://localhost:6379/2"


def test_configure_xdist_worker_environment_rewrites_urls(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
    monkeypatch.setenv(
        "TEST_DATABASE_URL", "postgresql://root:password@localhost:5432/test"
    )
    monkeypatch.setenv("TEST_REDIS_URL", "redis://localhost:6379/2")

    configure_xdist_worker_environment()

    assert (
        os.environ["TEST_DATABASE_URL"]
        == "postgresql://root:password@localhost:5432/test_xdist_3"
    )
    assert (
        os.environ["TEST_REDIS_URL"] == f"redis://localhost:6379/{REDIS_DB_OFFSET + 3}"
    )
