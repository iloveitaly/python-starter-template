"""
Asking for trouble using a standard name like this :/
"""

from pathlib import Path


def get_root_path():
    return Path(__file__).parent.parent


def modules_in_folder(base_path, package_prefix):
    """
    Iterator that yields all modules 'beneath' a particular folder

    package_prefix should be set to __package__ and is most likely formatted something like
    `app.models`.

    Args:
        base_path: Path object pointing to the directory to search
        package_prefix: Optional package prefix for the module names

    Yields:
        Fully qualified module names as strings
    """

    for py_file in base_path.rglob("*.py"):
        if py_file.name in ["__init__.py", "__main__.py"]:
            continue

        rel_path = py_file.relative_to(base_path)
        module_parts = rel_path.with_suffix("").parts
        module_name = f"{package_prefix}." + ".".join(module_parts)
        yield module_name
