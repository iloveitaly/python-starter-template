#!/usr/bin/env -S uv run ipython -i

# isort: off

import ipython_playground

# general utilities
import funcy_pipe as fp

# aliases for query building
from sqlmodel import SQLModel, select
import sqlalchemy as sa
import sqlmodel as sm

# autoimport packages
import app.models
import app.commands
import app.jobs

from app.configuration.clerk import clerk

from app.configuration.database import database_url
from activemodel import SessionManager
from activemodel.utils import find_all_sqlmodels
from activemodel.session_manager import _session_context
from sqlmodel import create_engine

# make all sqlmodels available in the repl
globals().update(find_all_sqlmodels(app.models))

# treat the entire ipython session as a with block :)
engine = create_engine(database_url(), echo=True)
session = SessionManager.get_instance().get_session().__enter__()
_session_context.set(session)

def sa_run(stmt):
      result = session.execute(stmt).all()
      return result

def sa_sql(stmt):
      return compile_sql(stmt)

ipython_playground.output()
