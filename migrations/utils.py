from alembic import op


def is_offline_migration() -> bool:
    """Return True when Alembic is running in offline (SQL-generation) mode.

    In offline mode there is no live database connection — Alembic emits raw SQL
    to stdout instead of executing against a real engine. This occurs when:

    - Running ``alembic upgrade --sql`` (or any ``--sql`` variant) to generate
      a SQL script for manual review or deployment.
    - Tools like alembic-squawk that invoke Alembic in offline mode to lint the
      generated SQL without touching a real database.

    In this mode ``op.get_bind()`` returns ``None``, so any code that touches
    the database (data migrations, ORM queries, etc.) must be skipped.
    """
    return op.get_context().as_sql
