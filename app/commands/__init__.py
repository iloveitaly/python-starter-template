"""
Commands are distinct from jobs: jobs are designed to be run by celery, commands can be run my jobs or by a user.

Auto-imports all modules in the commands directory and subdirectories and validates that each module has a 'perform' method.
"""

from types import ModuleType

from app.setup import autoimport_submodules


def _validate_command_module(module_name: str, module: ModuleType) -> None:
    # validate that the module has a 'perform' method, this is a convention in this folder
    if not hasattr(module, "perform") or not callable(module.perform):
        raise AttributeError(
            f"Module {module_name} must have a callable 'perform' method"
        )


autoimport_submodules(on_import=_validate_command_module)
