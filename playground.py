#!/usr/bin/env -S uv run ipython -i
# isort: off

import ipython_playground

from app.configuration.clerk import clerk

globals().update(ipython_playground.all_extras())

ipython_playground.output()
