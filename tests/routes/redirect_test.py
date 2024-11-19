from decouple import config
from fastapi.testclient import TestClient

from app.server import app


def test_https_redirection():
    original_base_url = config("VITE_PYTHON_URL", cast=str)

    # convert protocol to http
    base_url = original_base_url.replace("https://", "http://")
    client = TestClient(app, base_url=base_url, follow_redirects=False)

    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["Location"] == original_base_url
