import json
from pathlib import Path

from decouple import config

from app.generated import fastapi_typed_routes, react_router_routes
from app.server import authenticated_api_app
from app.utils.openapi import generate_openapi_schema
from tests.utils import run_just_recipe


def test_openapi_schema_matches_generated_file():
    generated_schema_path = config(
        "OPENAPI_JSON_PATH", default="web/openapi.json", cast=str
    )
    assert generated_schema_path

    # Read the file content
    generated_schema = json.loads(Path(generated_schema_path).read_text())

    # Use our utility function instead of direct call
    current_schema = generate_openapi_schema(authenticated_api_app)

    assert current_schema == generated_schema, (
        "OpenAPI schema from FastAPI doesn't match the generated file. Run:\njust js_generate-openapi"
    )


def test_generated_files_match_just_py_generate():
    assert fastapi_typed_routes.__file__
    assert react_router_routes.__file__

    fastapi_target_file = Path(fastapi_typed_routes.__file__)
    react_router_target_file = Path(react_router_routes.__file__)

    assert fastapi_target_file.exists()
    assert react_router_target_file.exists()

    fastapi_original_content = fastapi_target_file.read_text()
    react_router_original_content = react_router_target_file.read_text()

    # Run generation using Just
    # This modifies the files in place
    run_just_recipe("_py_generate")

    fastapi_new_content = fastapi_target_file.read_text()
    react_router_new_content = react_router_target_file.read_text()

    assert fastapi_new_content == fastapi_original_content, (
        "FastAPI typed routes do not match the generated file. Run:\njust py_generate"
    )

    assert react_router_new_content == react_router_original_content, (
        "React router routes do not match the generated file. Run:\njust py_generate"
    )
