"""
Application helpers (integrations and higher-level utilities).

May depend on models and lib. Prefer not depending on commands or generated.
Auto-imports all modules in this package so startup fails fast on import errors.
"""

from app.setup import autoimport_submodules

autoimport_submodules()
