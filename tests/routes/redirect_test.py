from fastapi.testclient import TestClient

from app.server import api_app
from tests.conftest import base_server_url


def test_https_redirection():
    client = TestClient(
        api_app, base_url=base_server_url("http"), follow_redirects=False
    )

    response = client.get(api_app.url_path_for("javascript_index"))

    assert response.status_code == 307
    assert response.headers["Location"] == base_server_url("https")
