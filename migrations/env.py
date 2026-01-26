# fmt: off

import os

# without importing the full alembic library, which would create
# an additional very unintuitive runtime dependency, we cannot determine
# if we are "in" an alembic migration or not. This ENV var let's us do this.
os.environ["ALEMBIC_MIGRATION"] = "true"

import hashlib
from logging.config import fileConfig

from sqlalchemy import engine_from_config, text
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.get_main_option("skip_logging_config") != "true" and config.config_file_name is not None:
    fileConfig(config.config_file_name)

import alembic_postgresql_enum
from sqlmodel import SQLModel
from app.models import *
from app.configuration.database import database_url

config.set_main_option("sqlalchemy.url", database_url())

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

ALEMBIC_LOCK_KEY = int.from_bytes(hashlib.sha256(b'alembic_lock').digest(), 'big') & ((1 << 64) - 1)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        cpu_count = (os.cpu_count() or 1) * 2

        with context.begin_transaction():
            # TODO a better solution here is prob defining a migration user, and then setting defaults on that user
            # to separate devops-type stuff from the application layer

            # https://github.com/sqlalchemy/alembic/issues/633
            # https://github.com/uc-cdis/fence/blob/cc2d0c966ffb8b3270531cfe88f4cdb3f3ee7972/migrations/env.py#L88
            # https://github.com/khulnasoft-lab/AiEXEC/blob/67e11c8b0e9f1d15b9a48db5c16b8f0a99f45d3c/api/base/aiexec/alembic/env.py#L88-L89
            # https://grok.com/share/bGVnYWN5_4a00f21a-78fe-4d8e-b412-f84ffa58659c
            connection.execute(text(f"""
            -- migrations shouldn't take more than 10m
            SET lock_timeout = '10min';
            -- may make migrations faster on larger tables, default is 64mb
            SET maintenance_work_mem = '4GB';
            -- creating indexes and other migration work can be parallelized
            SET max_parallel_maintenance_workers = '{cpu_count}';
            -- this is per query, which is we don't use the 4GB value above
            SET work_mem = '1GB';

            -- now, let's grab the distributed lock for running the migrations
            SELECT pg_advisory_xact_lock({ALEMBIC_LOCK_KEY});
            """))
            log.info("acquired advisory lock")

            context.run_migrations()


if context.is_offline_mode():
    # `alembic check` is an example of when offline mode is used
    run_migrations_offline()
else:
    run_migrations_online()
