# isort: off

import typing as t
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel

from app.configuration.database import get_engine


def truncate_db():
    # TODO Problem with truncation is you can't run multiple tests in parallel without separate containers

    print("Truncating database")

    exception_tables = ["alembic_version", "zip_code", "random_address"]

    with get_engine().connect() as connection:
        for table in reversed(SQLModel.metadata.sorted_tables):
            transaction = connection.begin()

            if table.name not in exception_tables:
                print("Truncating", table.name)
                connection.execute(table.delete())

            transaction.commit()


truncate_db()


CLEANER_STRATEGY: t.Literal["truncate", "session"] = "truncate"


if CLEANER_STRATEGY == "truncate":

    @pytest.fixture(scope="session", autouse=True)
    def truncate_db_tests():
        """
        Problem with truncation is you can't run multiple tests in parallel
        """

        truncate_db()

        yield


if CLEANER_STRATEGY == "session":

    @pytest.fixture(scope="session", autouse=True)
    def reset_db():
        """
        https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created
        https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
        https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77
        https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46
        """

        engine = get_engine()

        with engine.begin() as connection:
            transaction = connection.begin_nested()
            session = Session(bind=connection)

            # oh baby, we like dangerous, don't we?
            # app.database.get_session = lambda: session
            # monkeypatch.setattr(app.database, "get_session", lambda: session)
            with patch.object(app.database, "_get_session", return_value=session):
                try:
                    yield
                finally:
                    transaction.rollback()
                    session.close()

    print("reset_db complete")


# TODO the problem with this approach is not every connection uses the same session
# @pytest.fixture(scope="session", autouse=True)
# def reset_db():
#     start_truncation_query = """
#         BEGIN;
#         SAVEPOINT test_truncation_savepoint;
#     """

#     raw_sql_exec(start_truncation_query)

#     yield

#     end_truncation_query = """
#         ROLLBACK TO SAVEPOINT test_truncation_savepoint;
#         RELEASE SAVEPOINT test_truncation_savepoint;
#         ROLLBACK;
#     """

#     raw_sql_exec(end_truncation_query)
#     print("reset_db complete!")
