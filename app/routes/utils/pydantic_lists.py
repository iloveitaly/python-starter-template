"""
TODO need to move to a better place

Pydantic doesn't have great solutions for lists of objects
"""

from types import GenericAlias
from typing import Any, cast

from pydantic import BaseModel, TypeAdapter


def _list_adapter[T: BaseModel](model: type[T]) -> TypeAdapter[list[T]]:
    # Pyright rejects a variable in a type expression (`list[model]`).
    return cast(
        TypeAdapter[list[T]], TypeAdapter(cast(Any, GenericAlias(list, (model,))))
    )


def validate_json_list[T: BaseModel](json_data: str | bytes, model: type[T]) -> list[T]:
    """Parse a JSON array into a list of `model` instances."""
    return _list_adapter(model).validate_json(json_data)


def dump_json_list[T: BaseModel](items: list[T], model: type[T] | None = None) -> bytes:
    """Serialize a list of models to JSON bytes. Infers `model` from `items[0]` if omitted."""
    if model is None:
        if not items:
            return b"[]"
        model = type(items[0])
    return _list_adapter(model).dump_json(items)


def dump_python_list[T: BaseModel](
    items: list[T], model: type[T] | None = None
) -> list[dict]:
    """Serialize a list of models to a list of dicts. Infers `model` from `items[0]` if omitted."""
    if model is None:
        if not items:
            return []
        model = type(items[0])
    return _list_adapter(model).dump_python(items)
