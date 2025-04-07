from decouple import config

import activemodel
from activemodel.session_manager import get_engine
from sqlmodel import SQLModel

from ..environments import is_development, is_production, is_staging, is_testing
from ..setup import get_root_path


def database_url():
    """
    This is also used by alembic logic as well, which is why it's extracted out
    """

    if is_testing():
        url = config("TEST_DATABASE_URL", cast=str)
    else:
        url = config("DATABASE_URL", cast=str)

    assert url.startswith("postgresql")

    # sqlalchemy does *not* allow to specify the dialect of the DB outside of the url protocol
    # https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
    # without this, psycopg2 would be used, which is not intended!
    return url.replace("postgresql://", "postgresql+psycopg://")


def configure_database():
    """
    The only configuration passed to active model, for now this project is tightly coupled
    so the defaults are exactly what we want.
    """

    if is_production() or is_staging():
        run_migrations()

    activemodel.init(database_url())


def create_db_and_tables():
    """
    Do not use when using alembic migrations, helpful for syncing the db during dev
    """

    assert is_testing() or is_development()
    assert len(SQLModel.metadata.tables.items()) > 0, "No tables found"

    SQLModel.metadata.create_all(get_engine())


def run_migrations():
    """
    Automatically run migrations. Here's why we do this:

    - Migrating automatically introduces some risk that an important migration happens without you watching it. However,
      it's up to the migration author to test their migration before merging it, so this shouldn't be an issue. Additionally
      the risk of *not* migrating automatically introduces additional manual steps for the developer, which is always risky.
    - When the new version of the application depends on a database migration, it's hard to *not* auto-migrate.
      In that scenario, the container will fail and roll back, which makes it challenging to actually run the migration.
      You have to have a container which does not have readiness probes in place (which introduces another set of problems)
    - If we auto-migrate, migration logs are sent to the logging system. If you shell into a container and migrate
      manually, the migration status does not get persisted to the logging system.
    """

    from alembic import command
    from alembic.config import Config

    from app import log

    log.info("running alembic migrations")

    alembic_cfg = Config(get_root_path() / "alembic.ini")
    command.upgrade(alembic_cfg, "head")
