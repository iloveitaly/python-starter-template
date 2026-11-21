#!/usr/bin/env -S ipython -i
# Description: production REPL, not designed to be used locally. `./console.py` in production.
# ruff: noqa: F401

# some common utilities that are a pain to reimplement
import json
import re
from urllib.parse import urlparse
from urllib.request import urlopen

import ipython_playground
from typeid import TypeID

# helpful shortcuts
from app import log
from app.configuration.clerk import clerk

HTTPS_SCHEME = "https"

globals().update(ipython_playground.all_extras())


def read_data_url(url):
    """
    Read a url with json, csv, etc and return the data.

    Helpful for pulling external data for one-off scripts
    """

    # convert start gist URLS to raw URLs
    if re.match(r"https://gist\.github\.com/", url):
        url = url.replace("gist.github.com", "gist.githubusercontent.com") + "/raw"

    assert urlparse(url).scheme == HTTPS_SCHEME, "only https urls are allowed"

    # scheme is asserted above; bandit still blacklists every urlopen call
    return urlopen(url).read()  # nosec B310


ipython_playground.output()
