"""Helpers for deriving unique URL slugs for SQLModel rows."""

from typing import Protocol

from slugify import slugify

from activemodel.query_wrapper import QueryWrapper


class SluggableModel(Protocol):
    @property
    def id(self) -> object: ...

    @property
    def name(self) -> str: ...

    @property
    def slug(self) -> str: ...

    @classmethod
    def where(cls, *conditions: object) -> QueryWrapper: ...


def _slug_row_exists(
    model_cls: type[SluggableModel], candidate: str, instance_id: object
) -> bool:
    slug_column = getattr(model_cls, "slug")
    id_column = getattr(model_cls, "id")

    query = model_cls.where(slug_column == candidate, id_column != instance_id)
    return query.exists()


def generate_slug(instance: SluggableModel) -> str | None:
    """
    Generate a unique slug for the given instance.

    None is returned if the instance has a non-blank slug or name.
    """
    if instance.slug.strip():
        return instance.slug

    name = instance.name.strip()
    if not name:
        return None

    model_cls = type(instance)
    base = slugify(name)
    if not base:
        return None

    candidate = base
    suffix = 2

    while _slug_row_exists(model_cls, candidate, instance.id):
        candidate = f"{base}-{suffix}"
        suffix += 1

    return candidate
