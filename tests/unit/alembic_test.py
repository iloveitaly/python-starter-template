"""
https://medium.com/exness-blog/alembic-migrations-without-downtime-a3507d5da24d
"""

from app.configuration.database import get_alembic_config, needs_alembic_migration


def test_only_single_head_revision_in_migrations():
    """Fail if the migration history has diverged into multiple heads."""

    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(get_alembic_config())

    # This will raise if there are multiple heads
    script.get_current_head()


def test_no_migration_needs_to_be_run():
    """Fail if the database is not already at the latest migration head."""

    assert not needs_alembic_migration()


def test_database_ahead_of_code_does_not_need_migration():
    """A database stamped with a revision this build doesn't have must NOT be
    treated as "needs migration".

    The rolling-deploy case: a newer container migrates, then an older one
    boots, sees an unknown revision, and tries to upgrade *from* it —
    `CommandError: Can't locate revision`.
    """

    from unittest.mock import patch

    from alembic.util.exc import CommandError

    real_config = get_alembic_config()

    class _AheadContext:
        @staticmethod
        def configure(_conn):
            return _AheadContext()

        def get_current_heads(self):
            return ("deadbeefcafe",)  # not in migrations/versions

    with patch(
        "alembic.runtime.migration.MigrationContext.configure",
        _AheadContext.configure,
    ):
        assert not needs_alembic_migration()

    # Sanity: the revision really is unresolvable, so the assertion above
    # isn't passing for an unrelated reason.
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(real_config)
    try:
        script.get_revision("deadbeefcafe")
        raise AssertionError("expected the fake revision to be unresolvable")
    except CommandError, KeyError:
        pass


def test_no_migration_needs_to_be_generated():
    """Fail if model metadata has drifted from the checked-in Alembic revisions."""

    from alembic import command

    command.check(get_alembic_config())
