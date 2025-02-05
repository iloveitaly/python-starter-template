#!/usr/bin/env -S ipython -i
# Description: production REPL, not designed to be used locally

from typeid import TypeID  # noqa: F401

import app.jobs
import app.models

from activemodel.utils import find_all_sqlmodels

# make all sqlmodels available in the repl
globals().update(find_all_sqlmodels(app.models))
