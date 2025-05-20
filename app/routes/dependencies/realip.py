from urllib.parse import parse_qsl

from starlette.requests import Request
from starlette.websockets import WebSocket

from app import log


async def client_ip_address(request: Request | WebSocket):
    """
    Get the client IP address from the request.

    Headers are not case-sensitive.

    Originally adapted from:
    https://github.com/long2ice/fastapi-limiter/blob/8d179c058fa2aaf98f3450c9026a7300ae2b3bdd/fastapi_limiter/__init__.py#L11
    """

    headers = request.headers

    for header in [
        "X-Forwarded-For",  # Standard, many proxies (nginx, AWS ELB, etc)
        "X-Real-IP",  # nginx, some other proxies
        "CF-Connecting-IP",  # Cloudflare
        "True-Client-IP",  # Akamai
        "Forwarded",  # RFC 7239 standard
    ]:
        value = headers.get(header)
        if not value:
            continue
        if header == "X-Forwarded-For":
            ip = value.split(",")[0].strip()
        elif header == "Forwarded":
            # Forwarded: for=192.0.2.60;proto=http;by=203.0.113.43
            forwarded_parts = dict(parse_qsl(value.replace(";", "&")))
            ip = forwarded_parts.get("for", "").strip()
        else:
            ip = value.strip()
        log.info("client ip header used", header=header)
        return ip

    if request.client:
        return request.client.host

    return None
