from starlette.requests import Request
from starlette.websockets import WebSocket


async def client_ip_address(request: Request | WebSocket):
    """
    Get the client IP address from the request.

    https://github.com/long2ice/fastapi-limiter/blob/8d179c058fa2aaf98f3450c9026a7300ae2b3bdd/fastapi_limiter/__init__.py#L11
    """
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        ip = forwarded.split(",")[0]
    else:
        ip = request.client.host

    return ip
