"""
For celery to properly pick up on all tasks they must all be imported when celery starts.

It's easier for us to auto-import all of them here, so Celery just needs to import app.jobs
"""

import importlib
from pathlib import Path

from app import log
from app.setup import modules_in_folder

for module_name in modules_in_folder(Path(__file__).parent, __package__):
    log.debug("auto importing", job=module_name)
    module = importlib.import_module(module_name)

    # validate that the module has a 'perform' method, this is a convention in this folder
    if not hasattr(module, "perform") or not callable(getattr(module, "perform")):
        raise AttributeError(
            f"Module {module_name} must have a callable 'perform' method"
        )
