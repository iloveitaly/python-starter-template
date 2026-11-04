"""
https://medium.com/exness-blog/alembic-migrations-without-downtime-a3507d5da24d
"""

from alembic import command
from alembic.runtime.migration import MigrationContext

from app.configuration.database import (
    get_alembic_config,
    needs_alembic_migration,
    run_migrations,
)


def test_only_single_head_revision_in_migrations():
    """Fail if the migration history has diverged into multiple heads."""

    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(get_alembic_config())

    # This will raise if there are multiple heads
    script.get_current_head()


def test_no_migration_needs_to_be_run():
    """Fail if the database is not already at the latest migration head."""

    assert not needs_alembic_migration()


def test_unknown_database_revision_skips_migrations(monkeypatch):
    """
    Skip migrations when the database is stamped with a revision missing from this build.

    - During rolling deploys or rollbacks, an older container can boot after a newer build has already migrated the database.
    - Alembic's `MigrationContext.get_current_heads()` reads `alembic_version` from the database, while `ScriptDirectory` only knows revisions checked into this build's `migrations/versions/`.
    - Returning `False` prevents `run_migrations()` from calling `command.upgrade`, which would otherwise raise `CommandError: Can't locate revision`.
    """

    monkeypatch.setattr(
        MigrationContext, "get_current_heads", lambda self: ("unknown_revision",)
    )

    assert not needs_alembic_migration()


def test_startup_rechecks_revisions_after_acquiring_lock(monkeypatch):
    """
    Recheck whether migrations are still needed after acquiring the Postgres advisory lock in `migrations/env.py`.

    - `run_migrations()` calls `needs_alembic_migration()` twice: once before `command.upgrade` (unlocked fast path) and once inside `migrations/env.py` after acquiring `pg_advisory_xact_lock`.
    - Monkeypatching `MigrationContext.get_current_heads` with an iterator simulates the database state changing while the container waits for the lock:
      1. The pre-lock check in `run_migrations()` consumes `()` (an unmigrated database behind head), so it proceeds into `command.upgrade` and `migrations/env.py`.
      2. The post-lock check in `migrations/env.py` consumes `("unknown_revision",)`, simulating a newer build having migrated the database while this container waited on the lock.
    - `migrations/env.py` sees `needs_alembic_migration() == False` and returns before `context.run_migrations()`, avoiding `CommandError: Can't locate revision`.
    """

    current_heads = iter([(), ("unknown_revision",)])
    monkeypatch.setattr(
        MigrationContext, "get_current_heads", lambda self: next(current_heads)
    )

    run_migrations()

    assert list(current_heads) == []


def test_no_migration_needs_to_be_generated():
    """Fail if model metadata has drifted from the checked-in Alembic revisions."""

    command.check(get_alembic_config())
