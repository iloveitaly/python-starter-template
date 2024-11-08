"""
Asking for trouble using a standard name like this :/
"""

import logging
from pathlib import Path

import openai
from decouple import RepositoryEmpty, config

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


def openai_logging_setup():
    """
    Config below is subject to change

    https://stackoverflow.com/questions/76256249/logging-in-the-open-ai-python-library/78214464#78214464
    https://github.com/openai/openai-python/blob/de7c0e2d9375d042a42e3db6c17e5af9a5701a99/src/openai/_utils/_logs.py#L16
    https://www.python-httpx.org/logging/

    Related gist: https://gist.github.com/iloveitaly/aa616d08d582c20e717ecd047b1c8534
    """

    openai_log_path = get_root_path() / "tmp/openai.log"
    openai_file_handler = logging.FileHandler(openai_log_path)

    openai_logger = logging.getLogger("openai")
    openai_logger.propagate = False
    openai_logger.handlers = []  # Remove all handlers
    openai_logger.addHandler(openai_file_handler)

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.propagate = False
    httpx_logger.handlers = []  # Remove all handlers
    httpx_logger.addHandler(openai_file_handler)


def configure_openai():
    openai.api_key = config("OPENAI_API_KEY", cast=str)
    openai_logging_setup()
