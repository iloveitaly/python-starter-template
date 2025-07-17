"""
https://grok.com/share/bGVnYWN5_4e2084c9-c940-4354-8ce1-2a058fefd0cd

would like to use python path syntax
"""
from fastapi import APIRouter
from fastapi.routing import APIRoute

class NamespacedAPIRouter(APIRouter):
    def __init__(self, *args, namespace: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace = namespace

    def add_api_route(self, path: str, endpoint, *, name: str = None, **kwargs):
        # If name is not provided, default to function name; then prefix with namespace
        if name is None:
            name = endpoint.__name__
        full_name = f"{self.namespace}:{name}" if self.namespace else name
        return super().add_api_route(path, endpoint, name=full_name, **kwargs)

# Usage
users_router = NamespacedAPIRouter(prefix="/users", namespace="users")

@users_router.get("/")
async def read_users():  # Name becomes "users:read_users" automatically
    return [{"username": "user1"}]
