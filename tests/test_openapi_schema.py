import json
from pathlib import Path

from app.server import app


def test_openapi_schema_matches_generated_file():
    web_dir = Path(__file__).parent.parent / "web"
    generated_schema_path = web_dir / "openapi.json"

    with open(generated_schema_path) as f:
        generated_schema = json.load(f)

    current_schema = app.openapi()

    assert (
        current_schema == generated_schema
    ), "OpenAPI schema from FastAPI doesn't match the generated file"
