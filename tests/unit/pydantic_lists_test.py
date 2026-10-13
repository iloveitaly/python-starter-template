from pydantic import BaseModel

from app.routes.utils.pydantic_lists import (
    dump_json_list,
    dump_python_list,
    validate_json_list,
)


class _Item(BaseModel):
    name: str


def test_validate_and_dump_json_list():
    items = validate_json_list(b'[{"name":"a"},{"name":"b"}]', _Item)

    assert [item.name for item in items] == ["a", "b"]
    assert dump_json_list(items) == b'[{"name":"a"},{"name":"b"}]'
    assert dump_python_list(items) == [{"name": "a"}, {"name": "b"}]


def test_dump_empty_lists_without_model():
    assert dump_json_list([]) == b"[]"
    assert dump_python_list([]) == []
