"""
For alembic to properly pick up on all model metadata all models must be imported here
"""

import importlib
import pkgutil

from app import log
from app.setup import get_root_path

for _, module_name, _ in pkgutil.iter_modules([str(get_root_path() / "app/models")]):
    log.debug(f"Importing: {__package__}.{module_name}")
    importlib.import_module(f"{__package__}.{module_name}")
