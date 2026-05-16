import pytest
from fastapi import status

from app.generated.fastapi_typed_routes import api_app_url_path_for


@pytest.mark.asyncio
async def test_security_headers_present(aclient):
    response = await aclient.get(api_app_url_path_for("healthcheck"))
    assert response.status_code == status.HTTP_200_OK

    headers = response.headers
    # Check for some common security headers added by 'secure'
    assert "strict-transport-security" in headers
    assert "x-frame-options" in headers
    assert "x-content-type-options" in headers
    assert "content-security-policy" in headers
    assert "referrer-policy" in headers
