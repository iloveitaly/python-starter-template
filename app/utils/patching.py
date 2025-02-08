"""
Utilities to help with monkey patching
"""


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()
