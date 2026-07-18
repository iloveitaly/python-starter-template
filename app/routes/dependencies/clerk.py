"""
Attempting to upstream at: https://github.com/clerk/clerk-sdk-python/pull/65/files
"""

import httpx2
from clerk_backend_api import AuthenticateRequestOptions, Clerk, RequestState
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import log

security = HTTPBearer()


class AuthenticateClerkRequest:
    """
    Protect a route or specific route:

    >>> from app.configuration.clerk import clerk
    >>> protected_router = APIRouter(
    >>>    prefix="/protected",
    >>>    dependencies=[Depends(AuthenticateClerkRequest(clerk))],
    >>> )

    Originally sourced from: https://github.com/clerk/clerk-sdk-python/issues/49
    """

    def __init__(self, clerk: Clerk):
        self.sdk = clerk

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> RequestState:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authenticated"
            )

        # Convert FastAPI request headers to a Requestish (headers mapping)
        httpx_request = httpx2.Request(
            method=request.method,
            url=str(request.url),
            headers=request.headers,
        )

        # Authenticate the request
        auth_state = self.sdk.authenticate_request(
            httpx_request,
            AuthenticateRequestOptions(),
        )

        # credentials were provided, and may even be valid clerk credentials, but may be stale which can cause them to fail the is_signed_in check
        if not auth_state.is_signed_in:
            log.warning(
                "clerk authentication failed",
                reason=auth_state.message,
                # TODO we aren't sure exactly what is in this payload at this point
                payload=auth_state.payload,
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=auth_state.message
            )

        # Attach the auth state to the request
        request.state.auth_state = auth_state

        return auth_state
