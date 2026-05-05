"""
For alembic to properly pick up on all model metadata all models must be imported here.

This imports all models in the current directory and subdirectories.
"""

from app.setup import autoimport_submodules

# Import all model modules so metadata is registered for migrations
autoimport_submodules()
