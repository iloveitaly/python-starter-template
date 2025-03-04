"""
Logic for an API server. This is distinct from the "app" API server, which hosts static assets
and is authenticated via a clerk token, and is meant to be consumed by an external user.


It is locked to a specific
TODO

- [ ] organizations? what is the clerk data model?
- [ ] use sk_ for API key prefix
"""

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.routing import Host

from sqlmodel import Field, SQLModel

# Configuration
ALLOWED_HOST = "api.example.com"  # Restrict to this host
API_KEY = "0123456789abcdef0123456789abcdef01234567"  # Hardcoded API key (use securely in production)

# Define the OAuth2 scheme for Bearer token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency to validate the API key
def validate_api_key(token: str = Depends(oauth2_scheme)):
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


authenticate_api_request_middleware = validate_api_key

external_api_app = APIRouter(
    prefix="/external/v1", dependencies=[Depends(authenticate_api_request_middleware)]
)


@external_api_app.get("/ping")
def external_api_ping():
    "basic uptime + API authentication check"
    return {"status": "ok"}


# Define the Item model using SQLModel
class Item(SQLModel):
    id: int = Field(default=None, primary_key=True)
    name: str


# Mock database (replace with a real database in production)
items = {2995104339: Item(id=2995104339, name="Sample Item")}
