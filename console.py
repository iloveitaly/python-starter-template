#!/usr/bin/env -S ipython -i
# Description: production REPL, not designed to be used locally. `./console.py` in production.
# isort: off

from typeid import TypeID  # noqa: F401

# autoimport packages
import app.models
import app.commands
import app.jobs

from app.configuration.clerk import clerk  # noqa: F401

from activemodel.utils import find_all_sqlmodels

# make all sqlmodels available in the repl
globals().update(find_all_sqlmodels(app.models))
