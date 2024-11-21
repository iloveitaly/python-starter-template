import json

from decouple import config

from app.server import api_app


def test_openapi_schema_matches_generated_file():
    generated_schema_path = config("OPENAPI_JSON_PATH", cast=str)
    assert generated_schema_path

    with open(generated_schema_path) as f:
        generated_schema = json.load(f)

    current_schema = api_app.openapi()

    assert (
        current_schema == generated_schema
    ), "OpenAPI schema from FastAPI doesn't match the generated file. Run:\njust js_generate-openapi"
