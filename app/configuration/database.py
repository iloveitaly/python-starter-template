from decouple import config
from redis.lock import LockError

from app.configuration.redis import get_redis

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

    # some environments (dokku) specify the DATABASE_URL as postgres://
    url = url.replace("postgres://", "postgresql://")

    assert url.startswith("postgresql")

    # sqlalchemy does *not* allow to specify the dialect of the DB outside of the url protocol
    # https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
    # without this, psycopg2 would be used, which is not intended!
    url = url.replace("postgresql://", "postgresql+psycopg://")

    return url


def configure_database():
    """
    The only configuration passed to active model, for now this project is tightly coupled
    so the defaults are exactly what we want.
    """

    # initialize before running migrations since the migration may need to use the database
    # for standard schema mutations, this should not occur, but if we interact with SQLModel using the session helpers
    # we need to have this set in order to use those (at least, for now).
    # TODO we should consider setting `init` manually in each migration that needs this and understand if running this
    # before a migration will cause an issue...
    activemodel.init(database_url())

    # TODO I wonder if this will cause issues with the system not picking up on required DB changes? We will see

    if is_production() or is_staging():
        run_migrations()


def create_db_and_tables():
    """
    Helpful for syncing in-progress models to the db during rapid development.

    Do not use when using alembic migrations. Running this will cause Alembic to miss important migrations
    since the latest changes are already in the database.
    """

    assert is_testing() or is_development()
    assert len(SQLModel.metadata.tables.items()) > 0, "No tables found"

    SQLModel.metadata.create_all(get_engine())


def run_migrations():
    """
    Run migrations 'inline', within the current process.

    Here's why we do this:

    - Migrating automatically introduces some risk that an important migration happens without you watching it. However,
      it's up to the migration author to test their migration before merging it, so this shouldn't be an issue. Additionally
      the risk of *not* migrating automatically introduces additional manual steps for the developer, which is always risky.
    - When the new version of the application depends on a database migration, it's hard to *not* auto-migrate.
      In that scenario, the container will fail and roll back, which makes it challenging to actually run the migration.
      You have to have a container which does not have readiness probes in place (which introduces another set of problems)
    - If we auto-migrate, migration logs are sent to the logging system. If you shell into a container and migrate
      manually, the migration status does not get persisted to the logging system.
    - Not all deployment platforms make it easy to run migrations in a container that has access to env vars.

    At one point, we implemented a distributed migration lock to wait on concurrent migrations. We removed this and moved
    to a migrations/env.py lock:

    - It required redis, which was another dependency in an environment that is often different than production
    - If the container was killed, the lock would not be released, which caused migrations to hang indefinitely on next
      deploy.

    """

    from alembic import command
    from alembic.config import Config

    from app import log

    log.info("running alembic migrations")

    alembic_cfg = Config(get_root_path() / "alembic.ini")
    alembic_cfg.set_main_option("skip_logging_config", "true")

    def needs_migration():
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        script_dir = ScriptDirectory.from_config(alembic_cfg)
        heads = script_dir.get_heads()

        with get_engine().connect() as conn:
            ctx = MigrationContext.configure(conn)
            current_heads = ctx.get_current_heads()
            return set(current_heads) != set(heads)

    # it's possible for this command to run concurrently if run on container start, which is the only way in some
    # environments. When this occurs, we should wait to acquire a distributed migration lock.
    # Ideally, we would know that the migration succeeded on the other box, but that would require digging in to the
    # Alembic internals, and it's easier just to run the migrations again which will result in a noop if another container
    # already executed the migrations.

    if needs_migration():
        command.upgrade(alembic_cfg, "head")
        log.info("migrations applied")
    else:
        log.info("no migrations needed")
