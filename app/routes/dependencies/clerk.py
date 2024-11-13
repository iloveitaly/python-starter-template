import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers.authenticaterequest import (
    AuthenticateRequestOptions,
    RequestState,
)
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class AuthenticateRequest:
    """
    Protect a route or specific route:

    >>> protected_router = APIRouter(
    >>>    prefix="/protected",
    >>>    dependencies=[Depends(AuthenticateRequest("clerk_secret_key"))],
    >>> )

    Originally sourced from: https://github.com/clerk/clerk-sdk-python/issues/49
    """

    def __init__(self, clerk_secret_key: str):
        self.clerk_secret_key = clerk_secret_key
        self.sdk = Clerk(bearer_auth=clerk_secret_key)

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> RequestState:
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Convert FastAPI request headers to httpx format
        httpx_request = httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )

        # Authenticate the request
        auth_state: RequestState = self.sdk.authenticate_request(
            httpx_request,
            AuthenticateRequestOptions(),
        )

        if not auth_state.is_signed_in:
            raise HTTPException(status_code=401, detail=auth_state.message)

        # Attach the auth state to the request
        request.state.auth_state = auth_state

        return auth_state