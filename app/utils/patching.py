"""
Utilities to help with monkey patching
"""


def hash_function_code(func):
    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()
