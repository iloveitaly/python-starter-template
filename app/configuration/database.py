from decouple import config
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, text

from ..environments import is_production, is_testing


def database_url():
    """
    This is also used by alembic logic as well, which is why it's extracted out
    """

    if is_testing():
        return config("TEST_DATABASE_URL", cast=str)
    else:
        return config("DATABASE_URL", cast=str)


_engine = None
_connection = None


def get_engine():
    global _engine

    if not _engine:
        _engine = create_engine(
            database_url(),
            echo=config("LOG_SQL", cast=bool, default=False),
        )

    return _engine


def clear_engine():
    global _engine, _connection

    if _engine:
        _engine.dispose()
        _engine = None
        _connection = None


# TODO not using this yet, but maybe this is better to avoid expiring sessions?
def get_connection():
    global _connection

    if not _connection:
        _connection = get_engine().connect()

    return _connection


def create_db_and_tables():
    """
    Do not use when using alembic migrations, helpful for syncing the db during dev
    """

    SQLModel.metadata.create_all(get_engine())


def _get_session():
    """
    Why this private method?

    So we can monkey patch effectively
    """
    return Session(get_engine())


def get_session():
    return _get_session()


def raw_sql_exec(raw_query: str):
    assert not is_production()

    with get_session() as session:
        session.execute(text(raw_query))
