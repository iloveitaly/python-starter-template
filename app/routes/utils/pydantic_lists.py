"""
TODO need to move to a better place

Pydantic doesn't have great solutions for lists of objects
"""

from pydantic import BaseModel, TypeAdapter


def validate_json_list[T: BaseModel](json_data: str | bytes, model: type[T]) -> list[T]:
    """Parse a JSON array into a list of `model` instances."""
    return TypeAdapter(list[model]).validate_json(json_data)


def dump_json_list[T: BaseModel](items: list[T], model: type[T] | None = None) -> bytes:
    """Serialize a list of models to JSON bytes. Infers `model` from `items[0]` if omitted."""
    if model is None:
        if not items:
            return b"[]"
        model = type(items[0])
    return TypeAdapter(list[model]).dump_json(items)
