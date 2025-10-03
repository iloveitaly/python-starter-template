#!/usr/bin/env -S ipython -i
# Description: production REPL, not designed to be used locally. `./console.py` in production.
# ruff: noqa: F401, F821

# some common utilities that are a pain to reimplement
import json
import re
from urllib.request import urlopen

import ipython_playground
from typeid import TypeID

# helpful shortcuts
from app import log
from app.configuration.clerk import clerk

globals().update(ipython_playground.all_extras())


def read_data_url(url):
    """
    Read a url with json, csv, etc and return the data.

    Helpful for pulling external data for one-off scripts
    """

    # convert start gist URLS to raw URLs
    if re.match(r"https?://gist\.github\.com/", url):
        url = url.replace("gist.github.com", "gist.githubusercontent.com") + "/raw"

    return urlopen(url).read()


ipython_playground.output()
