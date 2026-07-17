"""
Client for resolving IP addresses to geographic locations.

Backed by observabilitystack/geoip-api:
https://github.com/observabilitystack/geoip-api
"""

import httpx2
from cachetools import LRUCache, cached
from pydantic import BaseModel

from app import log
from app.env import env
from app.models.data.geolocation_point import GeolocationPoint

GEOIP_BASE_URL = env.str("GEOIP_BASE_URL")
assert GEOIP_BASE_URL.endswith("/"), "GEOIP_BASE_URL must end with a trailing slash"

# Autocomplete must stay snappy; skip location bias if geoip is slow.
GEOIP_TIMEOUT_SECONDS = 0.1

# Arbitrary bound so unique IPs cannot grow memory without limit.
_geoip_cache: LRUCache = LRUCache(maxsize=1024)
_geoip_client = httpx2.Client(
    base_url=GEOIP_BASE_URL,
    timeout=GEOIP_TIMEOUT_SECONDS,
)


class GeoIPLocation(BaseModel):
    """Response payload from the geoip API (field names match the API)."""

    country: str | None = None
    stateprov: str | None = None
    stateprovCode: str | None = None
    city: str | None = None
    latitude: float
    longitude: float
    continent: str | None = None
    timezone: str | None = None
    usMetroCode: int | None = None
    accuracyRadius: int | None = None
    asn: int | None = None
    asnOrganization: str | None = None
    asnNetwork: str | None = None

    def to_geolocation_point(self) -> GeolocationPoint:
        return GeolocationPoint(
            lat=self.latitude,
            lon=self.longitude,
            city=self.city,
            state=self.stateprov,
            state_code=self.stateprovCode,
            country_code=self.country,
        )


@cached(cache=_geoip_cache)
def lookup_ip_location(ip: str) -> GeoIPLocation | None:
    """
    Resolve an IP address to lat/lng via the geoip API.

    Results are memoized in-process. On timeout (>100ms), network errors, or
    non-success responses, returns None so callers can proceed without bias.
    """
    try:
        response = _geoip_client.get(f"/{ip}")
        response.raise_for_status()
        return GeoIPLocation.model_validate(response.json())
    except httpx2.TimeoutException:
        log.warning("geoip lookup timed out", ip=ip, timeout=GEOIP_TIMEOUT_SECONDS)
        return None
    except Exception as e:
        log.warning("geoip lookup failed", ip=ip, error=str(e))
        return None


def get_point_for_ip(ip: str | None) -> GeolocationPoint | None:
    """
    Return a GeolocationPoint for an IP, or None if unavailable / too slow.
    """
    if not ip:
        return None

    location = lookup_ip_location(ip)
    if location is None:
        return None

    return location.to_geolocation_point()
