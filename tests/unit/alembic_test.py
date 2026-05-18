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


def test_no_migration_needs_to_be_generated():
    """Fail if model metadata has drifted from the checked-in Alembic revisions."""

    from alembic import command

    command.check(get_alembic_config())
