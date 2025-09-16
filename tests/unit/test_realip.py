from fastapi import Request

from app.routes.dependencies.realip import client_ip_from_request


def make_request(
    *,
    headers: dict[str, str] | None = None,
    client_host: str = "203.0.113.10",
    client_port: int = 5150,
) -> Request:
    header_items: list[tuple[bytes, bytes]] = []
    if headers:
        for k, v in headers.items():
            header_items.append((k.lower().encode(), v.encode()))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "server": ("example.com", 443),
        "client": (client_host, client_port),
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": header_items,
    }

    return Request(scope)


def test_x_forwarded_for_prefers_first_ipv4():
    request = make_request(
        headers={
            "X-Forwarded-For": "203.0.113.5, 70.41.3.18, 150.172.238.178",
        }
    )

    assert client_ip_from_request(request) == "203.0.113.5"


def test_forwarded_header_parsing_ipv4():
    request = make_request(
        headers={
            "Forwarded": "for=192.0.2.60;proto=http;by=203.0.113.43",
        }
    )

    assert client_ip_from_request(request) == "192.0.2.60"


def test_header_precedence_prefers_x_forwarded_for_over_x_real_ip():
    request = make_request(
        headers={
            "X-Real-IP": "203.0.113.99",
            "X-Forwarded-For": "198.51.100.23",
        }
    )

    assert client_ip_from_request(request) == "198.51.100.23"


def test_cf_connecting_ip_used_when_no_xff():
    request = make_request(
        headers={
            "CF-Connecting-IP": "198.51.100.42",
        }
    )

    assert client_ip_from_request(request) == "198.51.100.42"


def test_fallback_to_client_host_ipv4_and_filtering():
    request = make_request(client_host="198.51.100.23")

    assert client_ip_from_request(request) == "198.51.100.23"
