from app.env import env

import activemodel
from activemodel import BaseModel
from activemodel.session_manager import get_engine
from sqlalchemy import inspect
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import Integer
from sqlmodel import SQLModel

from ..environments import is_development, is_testing
from ..setup import get_root_path


def database_url():
    """
    This is also used by alembic logic as well, which is why it's extracted out
    """

    if is_testing():
        url = env.str("TEST_DATABASE_URL")
    else:
        url = env.str("DATABASE_URL")

    # some environments (dokku) specify the DATABASE_URL as postgres://
    url = url.replace("postgres://", "postgresql://")

    assert url, "Database URL is empty"
    assert url.startswith("postgresql"), "Database URL must start with postgresql"

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

    # no reason BIGINT shouldn't be the default, this satisfies the squawk errors
    @compiles(Integer, "postgresql")
    def compile_bigint(type_, compiler, **kw):
        return "BIGINT"

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


def get_alembic_config():
    """
    Build the Alembic config used for migration checks and upgrades."

    This is used (a) to run production migrations and (b) run migration assertions in tests.
    """

    from alembic.config import Config

    alembic_cfg = Config(get_root_path() / "alembic.ini")
    alembic_cfg.set_main_option("skip_logging_config", "true")
    return alembic_cfg


def needs_alembic_migration() -> bool:
    """
    Return whether the connected database is behind the checked-in Alembic heads.

    Alembic tracks a DAG of revisions, so we compare all current heads rather than
    assuming a single linear tip. However, our application should only ever use a single linear tip.
    """

    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    from app import log

    script_dir = ScriptDirectory.from_config(get_alembic_config())
    heads = script_dir.get_heads()

    with get_engine().connect() as conn:
        ctx = MigrationContext.configure(conn)
        current_heads = ctx.get_current_heads()

    needs_migration = set(current_heads) != set(heads)

    if needs_migration:
        log.info("migrations needed", current_heads=current_heads, heads=heads)
    else:
        log.info("no migrations needed", current_heads=current_heads, heads=heads)

    return needs_migration


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

    from app import log

    engine = get_engine()

    # the table name *could* be different than the connection url, but not for us!
    log.info("running alembic migrations", database_name=engine.url.database)

    # It's possible for this command to run concurrently if run on container start, which is the only way in some
    # production environments. When this occurs, we should wait to acquire a distributed migration lock before running migrations
    # to avoid running the same migration at the same time. This is not done automatically by Alembic.
    #
    # The distributed lock is *not* managed by redis, but instead we use a built-in distributed lock functionality in Postgres.
    # This is implemented in the migrations/env.py file, so that however alembic migrations are run the same locking functionality is used.
    #
    # Ideally, we would know that the migration succeeded on the other box, but that would require digging in to the
    # Alembic internals, and it's easier just to run the migrations again here, which will result in a noop if another container
    # already executed the migrations. This is why we just `command.upgrade` after checking if migrations should be run.

    if needs_alembic_migration():
        command.upgrade(get_alembic_config(), "head")


# TODO remove once this exists upstream in ActiveModel
def table_exists(model: type[SQLModel]) -> bool:
    """
    Check if the table for the given model exists in the database.
    """
    engine = get_engine()
    return inspect(engine).has_table(str(model.__tablename__))


# TODO look into merging into AM upstream
def is_database_empty(exclude: list[type[SQLModel]] = []) -> bool:
    """
    Check if any table in the database has records using Model.count().

    Useful for detecting an empty database state to run operations such as seeding, etc.
    """

    from app import log

    # TODO should try the new fp typed stuff here
    # Get all subclasses recursively
    all_models = BaseModel.__subclasses__()
    for model in all_models:
        all_models.extend(model.__subclasses__())

    for model_cls in all_models:
        if model_cls in exclude:
            log.info("skipping table in empty check", table=model_cls.__tablename__)
            continue

        # TODO there's not to be a better way to do this?
        # Only check classes that are actual tables
        if not getattr(model_cls, "__tablename__", None):
            continue

        count = model_cls.count()
        if count > 0:
            log.warning(
                "table is not empty",
                table=model_cls.__tablename__,
                record_count=count,
            )
            return False

    return True
