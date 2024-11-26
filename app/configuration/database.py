import activemodel
from activemodel.session_manager import get_engine
from decouple import config
from sqlmodel import SQLModel, text

from ..environments import is_development, is_production, is_testing


def database_url():
    """
    This is also used by alembic logic as well, which is why it's extracted out
    """

    if is_testing():
        return config("TEST_DATABASE_URL", cast=str)
    else:
        return config("DATABASE_URL", cast=str)


def configure_database():
    """
    The only configuration passed to active model, for now this project is tightly coupled
    so the defaults are exactly what we want.
    """

    activemodel.init(database_url())


def create_db_and_tables():
    """
    Do not use when using alembic migrations, helpful for syncing the db during dev
    """

    assert is_testing() or is_development()
    assert len(SQLModel.metadata.tables.items()) > 0, "No tables found"

    SQLModel.metadata.create_all(get_engine())
