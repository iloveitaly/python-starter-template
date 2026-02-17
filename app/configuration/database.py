from decouple import config

import activemodel
from activemodel.session_manager import get_engine
from sqlmodel import SQLModel

from ..environments import is_development, is_testing
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
    Run migrations within the current process.

    Migrating automatically introduces risk that an important migration happens without you watching it. However,
    it's up to the migration author to test their migration before merging it, so this shouldn't be an issue.

    Here's why you may want to do this:

    - The risk of *not* migrating automatically introduces additional manual steps for the developer, which is always risky.
    - When the new version of the application depends on a database migration, it's hard to *not* auto-migrate. Unless
      migrations are carefully staged so application code does not depend on them, you have to migrate before launching
      a new container depending on those migrations. If you don't, the container will fail and roll back, which makes
      it challenging to actually run the migration. You have to have a container that does not have readiness probes
      in place (which introduces another set of problems) in order to run the migration.
    - If we auto-migrate, migration logs are sent to the logging system. If you shell into a container and migrate
      manually, the migration status does not get persisted to the logging system.
    - Not all deployment platforms make it easy to run migrations in a container that has access to env vars.

    For this reason, while an application is simple and the database is small, we recommend auto-migrating on startup.
    We've experimented with a bunch of places to do this, and here's what we recommend:

    - Run this migration logic during the setup() call right after setup() is marked as run
    - Start the container ideally in a pre-start hook or as the entrypoint command. If this isn't possible, running it
      on container startup works, but will cause issues with liveness probes timing out for larger migrations.

    At one point, we implemented a distributed migration lock to wait on concurrent migrations. We removed this and moved
    to a migrations/env.py lock in postgres instead of a redis-based distributed lock. Here's why:

    - It required redis, which was another dependency in an environment that is often different than production
    - If the container was killed, the lock would not be released, which caused migrations to hang indefinitely on next
      deploy.

    """

    from alembic import command
    from alembic.config import Config

    from app import log

    engine = get_engine()

    # the table name *could* be different than the connection url, but not for us!
    log.info("running alembic migrations", database_name=engine.url.database)

    alembic_cfg = Config(get_root_path() / "alembic.ini")
    alembic_cfg.set_main_option("skip_logging_config", "true")

    def needs_migration():
        """
        In alembic, there isn't necessarily a single tip. This is why it's `heads` not `head`.

        The alembic migration data model is a DAG, not a linked list, but in practice for us it should be a simple linked
        list so we treat it as such.
        """
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        script_dir = ScriptDirectory.from_config(alembic_cfg)
        heads = script_dir.get_heads()

        with get_engine().connect() as conn:
            ctx = MigrationContext.configure(conn)
            current_heads = ctx.get_current_heads()

            if needs_migration := set(current_heads) != set(heads):
                log.info("migrations needed", current_heads=current_heads, heads=heads)
            else:
                log.info(
                    "no migrations needed", current_heads=current_heads, heads=heads
                )

            return needs_migration

    # it's possible for this command to run concurrently if run on container start, which is the only way in some
    # environments. When this occurs, we should wait to acquire a distributed migration lock.
    # Ideally, we would know that the migration succeeded on the other box, but that would require digging in to the
    # Alembic internals, and it's easier just to run the migrations again which will result in a noop if another container
    # already executed the migrations.

    if needs_migration():
        command.upgrade(alembic_cfg, "head")
