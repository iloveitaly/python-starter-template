import os

from sqlalchemy.engine import make_url

from .log import log


def get_worker_database_name(worker_id: str | int) -> str:
    """
    Generate a unique, easily identifiable database name for a given pytest-xdist worker.
    """
    if isinstance(worker_id, str) and worker_id.startswith("gw"):
        worker_num = worker_id.replace("gw", "")
    else:
        worker_num = str(worker_id)

    return f"pytest_worker_{worker_num}_test"


def configure_xdist_worker_environment() -> None:
    """
    Configures the environment for xdist workers *before* any other imports or setup.
    This ensures that when the app is initialized, it connects to the correct database and redis instance.
    """
    worker_id_env = os.getenv("PYTEST_XDIST_WORKER")
    if not worker_id_env:
        return

    from app.env import env  # Import here to avoid circularity if imported early

    worker_db_name = get_worker_database_name(worker_id_env)
    worker_num = int(worker_id_env.replace("gw", ""))

    # Configure unique database for this worker
    original_db_url_str = env.str("TEST_DATABASE_URL")
    original_db_url = make_url(original_db_url_str)

    # We must modify os.environ directly because app.env.env reads from it
    # AND we must do it before app.models is imported
    worker_db_url = original_db_url.set(database=worker_db_name)
    os.environ["TEST_DATABASE_URL"] = worker_db_url.render_as_string(hide_password=False)

    # Configure unique redis for this worker
    # Each worker gets its own redis database index to avoid collisions
    # Redis supports 16 databases by default (0-15)
    # We'll use 2+ to avoid conflict with default test db (1) and potential others
    # Assuming max 8 workers, this gives us range 2-9
    worker_redis_db = str(2 + worker_num)

    original_redis_url_str = env.str("TEST_REDIS_URL")

    # Redis URL parsing. make_url doesn't natively fully support redis database index nicely as the database,
    # but it works well enough since the database is just the path part.
    original_redis_url = make_url(original_redis_url_str)
    worker_redis_url = original_redis_url.set(database=worker_redis_db)

    os.environ["TEST_REDIS_URL"] = worker_redis_url.render_as_string(hide_password=False)

    log.info(
        "configured xdist worker environment",
        worker_id=worker_id_env,
        db_url=os.environ["TEST_DATABASE_URL"],
        redis_db=os.environ["TEST_REDIS_URL"]
    )


def setup_xdist_worker_databases(num_processes: int | str) -> None:
    """
    Create the template databases for the workers to use. This expects to be run in the master
    pytest process, after the primary `test` database has been fully initialized/migrated/truncated.
    """

    # If config.option.numprocesses exists, xdist has likely already evaluated "auto" to an integer.
    # If not, we can safely fall back to logical cpu count.
    if isinstance(num_processes, int):
        count = num_processes
    else:
        count = os.cpu_count() or 4

    log.info("preparing xdist worker databases", worker_count=count)

    from activemodel.session_manager import get_engine
    from sqlalchemy import create_engine, text

    engine = get_engine()
    current_db = engine.url.database

    # Explicitly ensure connections are released before creating template databases
    # since postgres will fail if there are any active connections to the template DB
    engine.dispose()

    # Connect specifically to the default 'postgres' database to perform operations on the test db
    # Doing this avoids active connections on the template database itself
    postgres_db_url = engine.url.set(database='postgres').render_as_string(hide_password=False)
    postgres_engine = create_engine(postgres_db_url, isolation_level="AUTOCOMMIT")

    try:
        with postgres_engine.connect() as conn:
            # Terminate any remaining connections to the template database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{current_db}'
                  AND pid <> pg_backend_pid();
            """))

            for i in range(count):
                worker_db_name = get_worker_database_name(i)

                # Drop if exists, disconnecting existing sessions
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{worker_db_name}'
                      AND pid <> pg_backend_pid();
                """))
                conn.execute(text(f"DROP DATABASE IF EXISTS {worker_db_name}"))

                # Create from template of the main test db
                log.info("creating worker database", worker_db=worker_db_name, template=current_db)
                conn.execute(text(f"CREATE DATABASE {worker_db_name} WITH TEMPLATE {current_db}"))
    except Exception as e:
        log.error("Failed to setup xdist databases", error=str(e))
        raise e
    finally:
        postgres_engine.dispose()
