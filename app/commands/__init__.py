"""
Commands are distinct from jobs: jobs are designed to be run by celery, commands can be run my jobs or by a user.

Auto-imports all modules in the commands directory and subdirectories and validates that each module has a 'perform' method.
"""

import importlib
from pathlib import Path

from app import log

commands_path = Path(__file__).parent

for py_file in commands_path.rglob("*.py"):
    if py_file.name in ["__init__.py", "__main__.py"]:
        continue

    rel_path = py_file.relative_to(commands_path)
    module_parts = rel_path.with_suffix("").parts
    module_name = f"{__package__}." + ".".join(module_parts)

    log.debug("auto importing", command=module_name)

    try:
        module = importlib.import_module(module_name)

        # Validate that the module has a 'perform' method
        if not hasattr(module, "perform") or not callable(getattr(module, "perform")):
            log.error(f"Module {module_name} doesn't have a 'perform' method")

    except Exception as e:
        log.error(f"Error importing module {module_name}: {str(e)}")
