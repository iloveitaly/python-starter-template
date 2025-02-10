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
