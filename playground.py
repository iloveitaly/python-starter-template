#!/usr/bin/env -S uv run ipython -i
# isort: off

import ipython_playground

# helpful shortcuts
from app import log
from app.configuration.clerk import clerk
from tests.factories import *

# additional utils
import funcy as fp
import funcy as f

globals().update(ipython_playground.all_extras())

ipython_playground.output()
