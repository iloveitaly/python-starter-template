"""
Patches to third party libraries to make them behave better in our environment.

Hopefully, there won't be many of these, but they should all live in a single location.
"""

import funcy_pipe


def configure_patches():
    funcy_pipe.patch()
