"""
Factories to quickly generate both test and dev (seed) data.

Notes on usage:

- Imports in this file allow factories to be automatically loaded into the console and playground
  without needing to import each factory manually.
- For correct type hints, factories must be imported using absolute imports,
  e.g. `from app.factories.user import UserFactory` instead of `from app.factories import UserFactory`.
"""

from app.environments import is_production
from app.setup import autoimport_submodules

if is_production():
    raise RuntimeError("app.factories should never be imported in production")

# export discovered factory symbols for console/playground
globals().update(dict(autoimport_submodules(collect_public_members=True)))
