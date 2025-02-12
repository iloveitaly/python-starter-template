"""
For celery to properly pick up on all tasks they must all be imported when celery starts.

It's easier for us to auto-import all of them here, so Celery just needs to import app.jobs
"""

import importlib
import pkgutil
from pathlib import Path

from app import log

for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).parent)]):
    log.debug("auto importing", job=f"{__package__}.{module_name}")
    importlib.import_module(f"{__package__}.{module_name}")
