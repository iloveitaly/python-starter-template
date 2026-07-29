"""Unit tests for the geoip client."""

import httpx2
import pytest

from app.utils import geoip
from app.utils.geoip import GeoIPLocation, get_point_for_ip, lookup_ip_location

SAMPLE_IP = "174.16.202.210"
SAMPLE_GEOIP_PAYLOAD = {
    "country": "US",
    "stateprov": "Colorado",
    "stateprovCode": "CO",
    "city": "Denver",
    "latitude": "39.7067",
    "longitude": "-104.9694",
    "continent": "NA",
    "timezone": "America/Denver",
    "usMetroCode": 751,
    "accuracyRadius": 20,
    "asn": 209,
    "asnOrganization": "CenturyLink Communications, LLC",
    "asnNetwork": "174.16.192.0/20",
}


@pytest.fixture(autouse=True)
def clear_geoip_cache():
    geoip._geoip_cache.clear()
    yield
    geoip._geoip_cache.clear()


def test_geoip_location_model_parses_api_payload():
    location = GeoIPLocation.model_validate(SAMPLE_GEOIP_PAYLOAD)

    assert location.latitude == pytest.approx(39.7067)
    assert location.longitude == pytest.approx(-104.9694)
    assert location.city == "Denver"
    assert location.stateprovCode == "CO"
    assert location.country == "US"
    assert location.asnOrganization == "CenturyLink Communications, LLC"


def test_lookup_ip_location_returns_parsed_location(httpx2_mock):
    httpx2_mock.add_response(json=SAMPLE_GEOIP_PAYLOAD)

    location = lookup_ip_location(SAMPLE_IP)

    assert location is not None
    assert location.latitude == pytest.approx(39.7067)
    assert location.longitude == pytest.approx(-104.9694)
    assert location.city == "Denver"


def test_lookup_ip_location_is_memoized(httpx2_mock):
    httpx2_mock.add_response(json=SAMPLE_GEOIP_PAYLOAD)

    first = lookup_ip_location(SAMPLE_IP)
    second = lookup_ip_location(SAMPLE_IP)

    assert first is second
    assert first is not None
    assert len(httpx2_mock.get_requests()) == 1


def test_lookup_ip_location_returns_none_on_timeout(httpx2_mock):
    httpx2_mock.add_exception(httpx2.TimeoutException("timed out"))

    assert lookup_ip_location("8.8.8.8") is None


def test_lookup_ip_location_returns_none_on_http_error(httpx2_mock):
    httpx2_mock.add_response(status_code=404)

    assert lookup_ip_location("127.0.0.1") is None


def test_get_point_for_ip_returns_none_without_ip():
    assert get_point_for_ip(None) is None


def test_get_point_for_ip_returns_geolocation_point(httpx2_mock):
    httpx2_mock.add_response(json=SAMPLE_GEOIP_PAYLOAD)

    point = get_point_for_ip(SAMPLE_IP)

    assert point is not None
    assert point.lat == pytest.approx(39.7067)
    assert point.lon == pytest.approx(-104.9694)
    assert point.city == "Denver"
    assert point.state == "Colorado"
    assert point.state_code == "CO"
    assert point.country_code == "US"
