"""
Factories to quickly generate both test and dev data.

Polyfactory is powerful, but dangerous.
Make sure you understand the nuances of how it works with pydantic
models.

Notes on usage:
    - Imports in this file allow factories to be automatically loaded into the console and playground
      without needing to import each factory manually.
    - For correct type hints, factories must be imported using absolute imports,
      e.g. `from tests.factories.user import UserFactory` instead of `from tests.factories import UserFactory`.
"""

import importlib
import inspect
from pathlib import Path

from app import log
from app.setup import modules_in_folder

for module_name in modules_in_folder(Path(__file__).parent, __package__):
    log.debug("auto importing", model=module_name)
    module = importlib.import_module(module_name)

    for name, obj in inspect.getmembers(module):
        """
        This is a bit hacky, but it allows us to automatically load all factories, functions
        into the console and playground without needing to import each factory manually.
        """
        if name.startswith("_"):
            # skip private members
            continue

        if inspect.ismodule(obj):
            # skip modules
            continue

        obj_module = getattr(obj, "__module__", None)
        if obj_module is None or obj_module != module.__name__:
            # skip members that are not defined in this module (e.g. imported members)
            # TODO it will skip defined constants
            continue

        globals()[name] = obj
