"""
Auto-import all jobs from one entrypoint.

For celery to properly pick up on all tasks they must all be imported when celery starts.

It's easier for us to auto-import all of them here, so Celery just needs to import app.jobs
"""

from types import ModuleType

from app.setup import autoimport_submodules


def _validate_job_module(module_name: str, module: ModuleType) -> None:
    # enforce that each module has a 'perform' method
    if not hasattr(module, "perform") or not callable(module.perform):
        raise AttributeError(
            f"Module {module_name} must have a callable 'perform' method"
        )


autoimport_submodules(on_import=_validate_job_module)
