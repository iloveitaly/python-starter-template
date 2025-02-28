"""
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


sync_router = APIRouter(prefix="/v1")


# Define the Item model using SQLModel
class Item(SQLModel):
    id: int = Field(default=None, primary_key=True)
    name: str


# Mock database (replace with a real database in production)
items = {2995104339: Item(id=2995104339, name="Sample Item")}


# Define the endpoint with API key validation
@sync_router.post("/items/get")
async def get_item(item_id: int = Form(...), _api: None = Depends(validate_api_key)):
    item = items.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item


# Mount the router under the specific host
sync_router = Host(ALLOWED_HOST, sync_router)
