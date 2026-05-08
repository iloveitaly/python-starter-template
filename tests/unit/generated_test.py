from pathlib import Path

import pytest

from app.env import env
from app.generated import fastapi_typed_routes, react_router_routes

from tests.direnv import run_just_recipe


def test_openapi_schema_matches_generated_file():
    # NOTE this is not set anywhere in the py codebase, which is why we need to manually source it here
    generated_schema_path = env.str("OPENAPI_JSON_PATH")
    assert generated_schema_path

    generated_schema_file = Path(generated_schema_path)
    assert generated_schema_file.exists()

    original_content = generated_schema_file.read_text()

    # This modifies the generated schema in-place, so we can re-read it and make sure the content has not changed.
    run_just_recipe("_js_generate")

    new_content = generated_schema_file.read_text()

    if new_content != original_content:
        # Use pytest.fail instead of assert to avoid verbose diff output for large generated files
        pytest.fail(
            "OpenAPI schema from FastAPI doesn't match the generated file. Run:\njust js_generate"
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

    # This modifies the generated files in-place, so we can re-read them and make sure the content has not changed
    run_just_recipe("_py_generate")

    fastapi_new_content = fastapi_target_file.read_text()
    react_router_new_content = react_router_target_file.read_text()

    if fastapi_new_content != fastapi_original_content:
        # Use pytest.fail instead of assert to avoid verbose diff output for large generated files
        pytest.fail(
            "FastAPI typed routes do not match the generated file. Run:\njust py_generate"
        )

    if react_router_new_content != react_router_original_content:
        # Use pytest.fail instead of assert to avoid verbose diff output for large generated files
        pytest.fail(
            "React router routes do not match the generated file. Run:\njust py_generate"
        )
