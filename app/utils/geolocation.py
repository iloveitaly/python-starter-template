"""
Geolocation utility functions for resolving IP addresses to geographic locations.
"""

import httpx

from app import log, root


def get_cached_public_ip() -> str | None:
    """
    Get the public IP address of the current machine, caching it in tmp/public-ip.
    Useful for development and testing to simulate a real client IP.
    """
    cache_file = root / "tmp/public-ip"

    if cache_file.exists():
        return cache_file.read_text().strip()

    try:
        # use a reliable external service to get the public IP
        response = httpx.get("https://checkip.amazonaws.com", timeout=5.0)
        response.raise_for_status()
        ip = response.text.strip()

        cache_file.write_text(ip)

        return ip
    except Exception as e:
        log.warning("failed to fetch public IP", error=str(e))
        return None
