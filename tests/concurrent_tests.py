"""Isolate pytest-xdist workers onto their own Postgres and Redis databases.

`app.setup()` reads `TEST_DATABASE_URL` / `TEST_REDIS_URL` and connects immediately,
so worker URLs must be rewritten before any `app` import.
"""

import os
import re
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from .log import log

WORKER_ID_PATTERN = re.compile(r"^gw(\d+)$")
WORKER_DATABASE_NAME_PATTERN = re.compile(r"^test_xdist_\d+$")

# Redis db 0 unused, db 1 development, db 2 default test / worker gw0.
# docker-compose redis is started with `--databases 128` to leave headroom for workers.
REDIS_DB_OFFSET = 2
REDIS_DATABASE_COUNT = 128


def xdist_worker_id() -> str | None:
    """Return this process's pytest-xdist worker id, or None on the controller.

    Workers set `PYTEST_XDIST_WORKER` (`gw0`, `gw1`, ...). The controller does not,
    which is how setup stays on the shared test database.
    """
    return os.environ.get("PYTEST_XDIST_WORKER")


def worker_index(worker_id: str) -> int:
    """Parse `gwN` into N so the database and Redis names match that worker.

    Anything other than an xdist id would rewrite the URL onto the wrong database.
    """
    match = WORKER_ID_PATTERN.fullmatch(worker_id)
    assert match, f"unexpected pytest-xdist worker id: {worker_id}"
    return int(match.group(1))


def worker_database_name(index: int) -> str:
    """Name the Postgres database cloned for worker N.

    The `test_xdist_` prefix is how leftover clones from an earlier run are found
    and dropped before this one creates them again.
    """
    assert index >= 0
    name = f"test_xdist_{index}"
    assert WORKER_DATABASE_NAME_PATTERN.fullmatch(name)
    return name


def replace_url_path(url: str, path: str) -> str:
    """Replace the database segment of a Postgres or Redis URL.

    Both `TEST_DATABASE_URL` and `TEST_REDIS_URL` store the database in the URL
    path, so one rewrite covers both.
    """
    parsed = urlparse(url)
    return urlunparse(parsed._replace(path=f"/{path}"))


def configure_xdist_worker_environment() -> None:
    """Point this worker at its own Postgres database and Redis logical DB.

    `app.setup()` reads those URLs at import time, so this has to run before any
    `app` import. No worker id means this is the controller, which keeps the
    shared test database.
    """
    worker_id = xdist_worker_id()
    if not worker_id:
        return

    index = worker_index(worker_id)
    redis_db = REDIS_DB_OFFSET + index
    assert redis_db < REDIS_DATABASE_COUNT, (
        f"xdist worker {index} needs redis db {redis_db}; "
        f"increase redis --databases (currently {REDIS_DATABASE_COUNT})"
    )

    os.environ["TEST_DATABASE_URL"] = replace_url_path(
        os.environ["TEST_DATABASE_URL"],
        worker_database_name(index),
    )
    os.environ["TEST_REDIS_URL"] = replace_url_path(
        os.environ["TEST_REDIS_URL"],
        str(redis_db),
    )

    log.info(
        "configured xdist worker environment",
        worker_id=worker_id,
        test_database_url=os.environ["TEST_DATABASE_URL"],
        test_redis_url=os.environ["TEST_REDIS_URL"],
    )


def setup_xdist_worker_databases(worker_count: int) -> None:
    """Clone the truncated test database for each xdist worker.

    Must run on the controller before workers start: `CREATE DATABASE ... TEMPLATE`
    cannot run concurrently against the same source database.
    """
    assert worker_count > 0

    from activemodel.session_manager import get_engine

    engine = get_engine()
    template_db = engine.url.database
    assert template_db

    engine.dispose()

    postgres_engine = create_engine(
        engine.url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    try:
        with postgres_engine.connect() as conn:
            _terminate_connections(conn, template_db)
            _drop_existing_xdist_databases(conn)

            for index in range(worker_count):
                name = worker_database_name(index)
                log.info(
                    "creating worker database",
                    worker_db=name,
                    template=template_db,
                )
                conn.execute(
                    text(f'CREATE DATABASE "{name}" WITH TEMPLATE "{template_db}"')
                )
    finally:
        postgres_engine.dispose()


def _terminate_connections(conn: Connection, database_name: str) -> None:
    """Disconnect every other session from `database_name`.

    Postgres refuses `CREATE DATABASE ... TEMPLATE` and `DROP DATABASE` while any
    session is still connected to that database.
    """
    conn.execute(
        text(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = :database_name
              AND pid <> pg_backend_pid()
            """
        ),
        {"database_name": database_name},
    )


def _drop_existing_xdist_databases(conn: Connection) -> None:
    """Drop leftover `test_xdist_*` databases from earlier runs.

    `CREATE DATABASE` fails if the clone name already exists, and a previous xdist
    run can leave those clones behind.
    """
    names = list(
        conn.execute(
            text(
                "SELECT datname FROM pg_database WHERE datname ~ '^test_xdist_[0-9]+$'"
            )
        ).scalars()
    )

    for name in names:
        assert WORKER_DATABASE_NAME_PATTERN.fullmatch(name)
        _terminate_connections(conn, name)
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
