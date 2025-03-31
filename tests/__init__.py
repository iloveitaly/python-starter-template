"""
Required in order for test helpers to be included *first* before test helpers defined in any editable packages.

Without this, tests/ folders in other packages could be picked up in addition to the tests here
causing all sorts of weird failures.
"""
