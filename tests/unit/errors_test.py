from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routes.errors import ClientError, register_exception_handlers


def test_client_error_default_status_and_code():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/error")
    def endpoint():
        raise ClientError("Something failed")

    client = TestClient(app)
    response = client.get("/error")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "Something failed",
        }
    }


def test_client_error_custom_status_code_and_code():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/custom")
    def endpoint():
        raise ClientError("Access forbidden", status_code=403, code="FORBIDDEN_CUSTOM")

    client = TestClient(app)
    response = client.get("/custom")

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "FORBIDDEN_CUSTOM",
            "message": "Access forbidden",
        }
    }


def test_http_exception_envelope_formatting():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/http-error")
    def endpoint():
        raise HTTPException(status_code=404, detail="Item not found")

    client = TestClient(app)
    response = client.get("/http-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Item not found",
        }
    }


def test_starlette_not_found_envelope_formatting():
    app = FastAPI()
    register_exception_handlers(app)

    client = TestClient(app)
    response = client.get("/nonexistent-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
        }
    }
