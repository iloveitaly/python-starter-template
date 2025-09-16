import json
from pathlib import Path

from decouple import config

from app.server import authenticated_api_app
from app.utils.openapi import generate_openapi_schema


def test_openapi_schema_matches_generated_file():
    generated_schema_path = config("OPENAPI_JSON_PATH", cast=str)
    assert generated_schema_path

    generated_schema = json.loads(Path(generated_schema_path).read_text())

    # Use our utility function instead of direct call
    current_schema = generate_openapi_schema(authenticated_api_app)

    assert current_schema == generated_schema, (
        "OpenAPI schema from FastAPI doesn't match the generated file. Run:\njust js_generate-openapi"
    )
