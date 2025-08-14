"""
TODO the reason there is a copy of this is we want to support ipv6 (helpful for FB tracking) but dokku/docker is not currently
setup for it, so i can't test this code.

Strangely enough there is not a library that does this for us.

We should consider contributing this to the community.

Should try this lib first:

https://github.com/un33k/python-ipware/tree/main

We also need to build this into the logging middleware on structlog
"""

from urllib.parse import parse_qsl
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Iterable

from starlette.requests import Request
from starlette.websockets import WebSocket

from app import log


def _extract_ip(token: str) -> str | None:
    """
    Normalize an address token to a bare IP, stripping quotes, brackets, and ports.
    Examples:
      '203.0.113.5' -> '203.0.113.5'
      '[2001:db8::1]:443' -> '2001:db8::1'
      '"[2001:db8::1]:1234"' -> '2001:db8::1'
    """
    value = token.strip().strip('"')

    if value.startswith("[") and "]" in value:
        value = value[1: value.index("]")]
        return value

    if ":" in value and value.count(":") == 1:
        host, _port = value.split(":", 1)
        return host

    return value


def _filter_by_version(candidates: Iterable[str], ip_version: str) -> str | None:
    for candidate in candidates:
        try:
            parsed = ip_address(candidate)
        except ValueError:
            continue

        if ip_version == "any":
            return candidate
        if ip_version == "ipv4" and isinstance(parsed, IPv4Address):
            return candidate
        if ip_version == "ipv6" and isinstance(parsed, IPv6Address):
            return candidate

    return None


def _forwarded_candidates(header_value: str) -> list[str]:
    candidates: list[str] = []
    for part in header_value.split(","):
        kv_pairs = [kv.strip() for kv in part.split(";") if kv.strip()]
        for kv in kv_pairs:
            if not kv.startswith("for="):
                continue
            _, raw = kv.split("=", 1)
            ip = _extract_ip(raw)
            if ip:
                candidates.append(ip)
                break
    return candidates


def client_ip_from_request(request: Request | WebSocket, *, ip_version: str = "any") -> str | None:
    """
    Get the client IP address from the request.

    Headers are not case-sensitive.

    Originally adapted from:
    https://github.com/long2ice/fastapi-limiter/blob/8d179c058fa2aaf98f3450c9026a7300ae2b3bdd/fastapi_limiter/__init__.py#L11
    """

    headers = request.headers

    # X-Forwarded-For may contain a list of IPs; select based on preferred version
    xff = headers.get("X-Forwarded-For")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        candidates = [_extract_ip(p) for p in parts]
        candidates = [c for c in candidates if c]
        selected = _filter_by_version(candidates, ip_version)
        if selected:
            log.info("client ip header used", header="X-Forwarded-For")
            return selected

    # RFC 7239 Forwarded header; can be a comma-separated list
    fwd = headers.get("Forwarded")
    if fwd:
        candidates = _forwarded_candidates(fwd)
        selected = _filter_by_version(candidates, ip_version)
        if selected:
            log.info("client ip header used", header="Forwarded")
            return selected

    # Simple single-address headers
    for header in [
        "X-Real-IP",
        "CF-Connecting-IP",
        "True-Client-IP",
    ]:
        value = headers.get(header)
        if not value:
            continue
        ip = _extract_ip(value)
        if not ip:
            continue
        selected = _filter_by_version([ip], ip_version)
        if selected:
            log.info("client ip header used", header=header)
            return selected

    host = getattr(request.client, "host", None)
    if not host:
        return None

    return _filter_by_version([host], ip_version)
