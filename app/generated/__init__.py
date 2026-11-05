"""
Generated code (typed routes, etc.). Consumers including commands may import from here.

Auto-imports all modules in this package so startup fails fast on import errors.
Note: fastapi_typed_routes imports app.server, so loading this package pulls in the web app.
"""

from app.setup import autoimport_submodules

autoimport_submodules()
