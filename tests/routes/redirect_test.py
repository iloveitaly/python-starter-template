from fastapi import status
from fastapi.testclient import TestClient

from app.server import api_app

from tests.routes.utils import base_server_url


def test_https_redirection():
    """
    Assumption is upstream proxy server will handle HTTPS redirection
    """

    client = TestClient(
        api_app, base_url=base_server_url("http"), follow_redirects=False
    )

    response = client.get(api_app.url_path_for("index"))

    assert response.status_code == status.HTTP_200_OK
