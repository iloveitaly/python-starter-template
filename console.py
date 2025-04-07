#!/usr/bin/env -S ipython -i
# Description: production REPL, not designed to be used locally. `./console.py` in production.
# noqa: F401

import json
import re
from urllib.request import urlopen

from typeid import TypeID  # noqa: F401

# autoimport packages
import app.commands
import app.jobs
import app.models

# helpful shortcuts
from app import log
from app.configuration.clerk import clerk  # noqa: F401

from activemodel.utils import find_all_sqlmodels

# make all sqlmodels available in the repl
globals().update(find_all_sqlmodels(app.models))


def read_data_url(url):
    "read a url with json, csv, etc and return the data"

    # convert start gist URLS to raw URLs
    if re.match(r"https?://gist\.github\.com/", url):
        url = url.replace("gist.github.com", "gist.githubusercontent.com") + "/raw"

    return urlopen(url).read()
