"""
Generate a URL slug segment from a SQLmodel row.
"""

from typing import Any, Protocol

from slugify import slugify

from activemodel.query_wrapper import QueryWrapper


class _SluggableModel(Protocol):
    # SQLModel fields are regular Python values on instances, but SQLAlchemy
    # descriptors on the model class. Pyright cannot represent that dual shape.
    id: Any
    slug: Any

    @property
    def name(self) -> str | None: ...

    @classmethod
    def where(cls, *conditions: object) -> QueryWrapper: ...

    def is_new(self) -> bool: ...


def _slug_row_exists(instance: _SluggableModel, candidate: str) -> bool:
    model_cls = instance.__class__
    conditions = [model_cls.slug == candidate]
    if not instance.is_new():
        conditions.append(model_cls.id != instance.id)

    return model_cls.where(*conditions).no_autoflush().exists()


def generate_slug(instance: _SluggableModel) -> str | None:
    """Return a unique slug from `name`, or `None` when nothing should be assigned.

    Returns `None` if a slug cannot be generated.
    """
    name = (instance.name or "").strip()
    if not name:
        return None

    base = slugify(name)
    if not base:
        return None

    candidate = base
    suffix = 2

    while _slug_row_exists(instance, candidate):
        candidate = f"{base}-{suffix}"
        suffix += 1

    return candidate
