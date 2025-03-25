"""
Asking for trouble using a standard name like this :/
"""

from pathlib import Path

from decouple import RepositoryEmpty

from app.utils.patching import hash_function_code


def get_root_path():
    return Path(__file__).parent.parent


def patch_decouple():
    """
    by default decouple loads from .env, but differently than direnv and other env sourcing tools
    let's remove automatic loading of .env by decouple
    """

    import decouple

    assert (
        hash_function_code(decouple.config.__class__)
        == "129ad6a4af2b57341101d668d2160549605b0a6bc04d4ae59f19beaa095e50d1"
    )

    # by default decouple loads from .env, but differently than direnv and other env sourcing tools
    # let's remove automatic loading of .env by decouple
    for key in decouple.config.SUPPORTED.keys():
        decouple.config.SUPPORTED[key] = RepositoryEmpty


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
