import inspect


def callable_file_line_reference(target: object) -> str | None:
    """Return a `file:line` source reference for a callable when available."""
    if not callable(target):
        return None

    try:
        file_path = inspect.getfile(target)
        line_number = inspect.getsourcelines(target)[1]
    except OSError, TypeError:
        return None

    return f"{file_path}:{line_number}"
