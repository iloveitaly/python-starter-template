import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import static


@pytest.fixture
def spa_app(tmp_path, monkeypatch):
    build = tmp_path / "client_build"
    # Required for mount_public_directory() to register the static routes.
    (build / "assets").mkdir(parents=True)
    # Must exist so the nested traversal reaches the secret with the original handler.
    (build / "nested").mkdir()
    # Expected response for traversal attempts and unknown SPA routes.
    (build / "index.html").write_text("<!doctype html><title>spa shell</title>")
    # Confirms ordinary files inside the build directory are still served.
    (build / "robots.txt").write_text("User-agent: *")
    # Existing file outside the build directory that traversal attempts must not expose.
    (tmp_path / "secret.txt").write_text("TOP SECRET")

    monkeypatch.setattr(static, "root", tmp_path)
    monkeypatch.setattr(static, "JAVASCRIPT_CLIENT_BUILD_DIR", "client_build")

    app = FastAPI()
    static.mount_public_directory(app)
    return app


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        # Encoding prevents the client from normalizing away the traversal.
        ("/%2e%2e/secret.txt", "<!doctype html><title>spa shell</title>"),
        (
            "/nested/%2e%2e/%2e%2e/secret.txt",
            "<!doctype html><title>spa shell</title>",
        ),
        ("/robots.txt", "User-agent: *"),
        ("/projects/some-id", "<!doctype html><title>spa shell</title>"),
    ],
)
def test_static_response(spa_app, path, expected):
    with TestClient(spa_app) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert response.text == expected
