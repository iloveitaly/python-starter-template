import os

import requests
from clerk_backend_api.jwks_helpers import AuthStatus
from clerk_backend_api.jwks_helpers.authenticaterequest import RequestState
from fastapi import Request

from app.configuration.clerk import CLERK_PRIVATE_KEY, clerk

from tests.utils import get_clerk_dev_user


class MockAuthenticateRequest:
    async def __call__(self, request: Request) -> RequestState:
        fake_auth_state = RequestState(
            status=AuthStatus.SIGNED_IN,
            reason=None,
            token="eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yb25uM1E3TkRmcndDNW9WWGd6R2U2dkExdTQiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE3MzY3ODk1ODgsImZ2YSI6Wy0xLC0xXSwiaWF0IjoxNzM2Nzg5NTI4LCJpc3MiOiJodHRwczovL3Jlc29sdmVkLWVtdS01My5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MzY3ODk1MTgsInNpZCI6InNlc3NfMnJhRnh2anVDUE5QRVFxaE8wdlFyMjVncjlvIiwic3ViIjoidXNlcl8ycmFGeHAzRENWUkZobnpqSlZpSDQ0Y2l2d3UifQ.DgnSSybWpG4ovKIDwDEvtnpMYOz8toWOJf8GXuftPIa0RiWp8EWpiX_m6fCTQBT3oCoR_BQXOEfTHtutzMYT5zmEL7FzDqBg_dE_dH9LJlq4s9WJ49pjWr1gfdMJF1okf0vdfROdKYnlCiKO4ocP1gM6s8hOPjRp_FTlFcj5bHhKSvRW63gmbeH-G-mZvxVkmXV7g9FeZ3idtSvzap8fBawYmhhqmtEa8-Re2Ikd1v3FxmnMcV2HPcKt1Kv9Vuo7oTC4_uMiX2MS-2EYt0Y5H6bkCyvbEmWmznIx2ZEnVQYFS36gpvjayEnr0uFK_jE1Uc7MIMgybueDqEcA1zqBjQ",
            payload={
                "exp": 1736789588,
                "fva": [-1, -1],
                "iat": 1736789528,
                # TODO should be dynamic
                "iss": "https://resolved-emu-53.clerk.accounts.dev",
                "nbf": 1736789518,
                "sid": "sess_2raFxvjuCPNPEQqhO0vQr25gr9o",
                "sub": "user_2raFxp3DCVRFhnzjJViH44civwu",
            },
        )
        # Attach the fake auth state to the request
        request.state.auth_state = fake_auth_state
        return fake_auth_state


def get_valid_token():
    _, _, user = get_clerk_dev_user()

    # now that we have a user, we need to create a session
    session = clerk.sessions.create_session(
        request={"user_id": "user_2sdUyAq37EEgJ4GOdh4ebw6aeta"}
    )
    assert session

    token = clerk.sessions.create_session_token(session_id=session.id)
    assert token

    return token.jwt
