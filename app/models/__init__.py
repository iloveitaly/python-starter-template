"""
For alembic to properly pick up on all model metadata all models must be imported here.

This imports all models in the current directory and subdirectories.
"""

import importlib
from pathlib import Path

from app import log

from ..setup import modules_in_folder

for module_name in modules_in_folder(Path(__file__).parent, __package__):
    log.debug("auto importing", model=module_name)
    importlib.import_module(module_name)
