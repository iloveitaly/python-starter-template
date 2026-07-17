"""
Geolocation utility functions for resolving IP addresses to geographic locations.
"""

import httpx

from app import log, root
from app.environments import is_productionish


def get_cached_public_ip() -> str | None:
    """
    Public IP for this machine, cached in tmp/public-ip. Dev/test only (None if productionish).

    Uncached fetches use checkip.amazonaws.com, which returns plain text: ``203.0.113.1\\n``.
    """
    if is_productionish():
        log.warning("get_cached_public_ip is not available in production-ish environments")
        return None

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
