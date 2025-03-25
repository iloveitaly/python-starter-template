"""
Commands are distinct from jobs: jobs are designed to be run by celery, commands can be run my jobs or by a user.

Auto-imports all modules in the commands directory and subdirectories and validates that each module has a 'perform' method.
"""

import importlib
from pathlib import Path

from app import log
from app.setup import modules_in_folder

for module_name in modules_in_folder(Path(__file__).parent, __package__):
    log.debug("auto importing", command=module_name)

    module = importlib.import_module(module_name)

    # validate that the module has a 'perform' method, this is a convention in this folder
    if not hasattr(module, "perform") or not callable(getattr(module, "perform")):
        raise AttributeError(
            f"Module {module_name} must have a callable 'perform' method"
        )
