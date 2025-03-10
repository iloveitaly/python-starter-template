"""
For alembic to properly pick up on all model metadata all models must be imported here.

This imports all models in the current directory and subdirectories.
"""

import importlib
from pathlib import Path

from app import log

models_path = Path(__file__).parent

for py_file in models_path.rglob("*.py"):
    if py_file.name in ["__init__.py", "__main__.py"]:
        continue

    rel_path = py_file.relative_to(models_path)
    module_parts = rel_path.with_suffix("").parts
    module_name = f"{__package__}." + ".".join(module_parts)
    log.debug("auto importing", model=module_name)
    importlib.import_module(module_name)
