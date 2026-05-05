"""
Asking for trouble using a standard name like this :/
"""

import importlib
import inspect
import logging
import pkgutil
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)


def get_root_path():
    return Path(__file__).parent.parent


def _public_members_from_module(module: ModuleType) -> list[tuple[str, object]]:
    members: list[tuple[str, object]] = []
    public_names = getattr(module, "__all__", None)

    if public_names is not None:
        # Respect explicit export contracts when modules define __all__.
        for name in public_names:
            if (
                not isinstance(name, str)
                or name.startswith("_")
                or not hasattr(module, name)
            ):
                continue

            obj = getattr(module, name)
            if inspect.ismodule(obj):
                continue

            members.append((name, obj))

        return members

    # Fallback: infer "public API" from symbols defined in this module.
    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        if inspect.ismodule(obj):
            continue

        obj_module = getattr(obj, "__module__", None)
        if obj_module is None or obj_module != module.__name__:
            continue

        members.append((name, obj))

    return members


def autoimport_submodules(
    strict: bool = True,
    *,
    include_packages: bool = False,
    on_import: Callable[[str, ModuleType], None] | None = None,
    collect_public_members: bool = False,
) -> list[tuple[str, object]]:
    """
    Auto-import every Python module in the calling package and subpackages.

    Call this from a package's `__init__.py` to ensure all submodules are loaded
    (useful for SQLModel metadata, Alembic, FastAPI routers, etc.).

    Args:
        strict: If True, halt on the first import failure. If False, log and continue.
        include_packages: When False, skip package modules (`__init__.py`) and only
            import non-package modules.
        on_import: Optional callback invoked after each successful import with
            `(module_name, module)`.
        collect_public_members: When True, return all public members discovered
            from imported modules.
    """
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back if current_frame is not None else None
    if caller_frame is None:
        raise RuntimeError("autoimport_submodules() could not determine the caller")

    # Explicitly remove stack-frame references to avoid leaks in long-lived processes
    # (e.g. hot reloaders and test runners) when import errors are caught/retried.
    try:
        module = inspect.getmodule(caller_frame)
        if module is None or not hasattr(module, "__path__"):
            raise RuntimeError(
                "autoimport_submodules() must be called from within a package __init__.py."
            )

        package_name = module.__name__
        package_path = module.__path__
        public_members: list[tuple[str, object]] = []

        for module_info in pkgutil.walk_packages(
            package_path, prefix=f"{package_name}."
        ):
            # Package __init__ modules are optional to avoid recursive/redundant imports.
            if module_info.ispkg and not include_packages:
                continue

            module_name = module_info.name

            try:
                imported_module = importlib.import_module(module_name)
                logger.debug("auto imported module: %s", module_name)

                # Hook allows each package to enforce conventions after import.
                if on_import is not None:
                    on_import(module_name, imported_module)

                # Optional export collection supports "autoload + symbol export" use cases.
                if collect_public_members:
                    public_members.extend(_public_members_from_module(imported_module))
            except Exception:
                logger.exception("failed to auto import module: %s", module_name)
                if strict:
                    raise

        return public_members
    finally:
        del current_frame
        del caller_frame
