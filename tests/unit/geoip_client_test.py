"""Unit tests for the geoip client."""

import httpx2
import pytest
from flexmock import flexmock

from app.utils import geoip
from app.utils.geoip import GeoIPLocation, get_point_for_ip, lookup_ip_location


@pytest.fixture(autouse=True)
def clear_geoip_cache():
    geoip._geoip_cache.clear()
    yield
    geoip._geoip_cache.clear()


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


def test_geoip_location_model_parses_api_payload():
    location = GeoIPLocation.model_validate(SAMPLE_GEOIP_PAYLOAD)

    assert location.latitude == pytest.approx(39.7067)
    assert location.longitude == pytest.approx(-104.9694)
    assert location.city == "Denver"
    assert location.stateprovCode == "CO"
    assert location.country == "US"
    assert location.asnOrganization == "CenturyLink Communications, LLC"


def test_lookup_ip_location_success():
    response = flexmock(
        raise_for_status=lambda: None,
        json=lambda: SAMPLE_GEOIP_PAYLOAD,
    )
    flexmock(geoip._geoip_client).should_receive("get").with_args(
        "/174.16.202.210"
    ).and_return(response).once()

    location = lookup_ip_location("174.16.202.210")

    assert location is not None
    assert location.latitude == pytest.approx(39.7067)
    assert location.longitude == pytest.approx(-104.9694)
    assert location.city == "Denver"


def test_lookup_ip_location_is_memoized():
    response = flexmock(
        raise_for_status=lambda: None,
        json=lambda: SAMPLE_GEOIP_PAYLOAD,
    )
    flexmock(geoip._geoip_client).should_receive("get").with_args(
        "/174.16.202.210"
    ).and_return(response).once()

    first = lookup_ip_location("174.16.202.210")
    second = lookup_ip_location("174.16.202.210")

    assert first is second
    assert first is not None


def test_lookup_ip_location_returns_none_on_timeout():
    flexmock(geoip._geoip_client).should_receive("get").and_raise(
        httpx2.TimeoutException("timed out")
    ).once()

    assert lookup_ip_location("8.8.8.8") is None


def test_lookup_ip_location_returns_none_on_http_error():
    def raise_status():
        raise httpx2.HTTPStatusError(
            "404",
            request=httpx2.Request("GET", "http://geoip.useverso.com/127.0.0.1"),
            response=httpx2.Response(404),
        )

    response = flexmock(raise_for_status=raise_status)
    flexmock(geoip._geoip_client).should_receive("get").and_return(response).once()

    assert lookup_ip_location("127.0.0.1") is None


def test_get_point_for_ip_helpers():
    assert get_point_for_ip(None) is None

    response = flexmock(
        raise_for_status=lambda: None,
        json=lambda: SAMPLE_GEOIP_PAYLOAD,
    )
    flexmock(geoip._geoip_client).should_receive("get").and_return(response).once()

    point = get_point_for_ip("174.16.202.210")
    assert point is not None
    assert point.lat == pytest.approx(39.7067)
    assert point.lon == pytest.approx(-104.9694)
    assert point.city == "Denver"
    assert point.state == "Colorado"
    assert point.state_code == "CO"
    assert point.country_code == "US"


def test_lookup_ip_location_live_api(monkeypatch):
    """
    Smoke test against the real geoip service for a known public IP.

    Uses a longer timeout than production so CI latency does not flake the check;
    production still enforces the 100ms budget on the autocomplete path.
    """
    live_client = httpx2.Client(base_url=geoip.GEOIP_BASE_URL, timeout=5.0)
    monkeypatch.setattr(geoip, "_geoip_client", live_client)

    # CenturyLink Denver residential IP used in the geoip service examples
    location = lookup_ip_location("174.16.202.210")

    assert location is not None
    assert location.country == "US"
    assert location.stateprovCode == "CO"
    assert location.city is not None
    assert 38 < location.latitude < 41  # Colorado latitude range
    assert -110 < location.longitude < -102  # Colorado longitude range

    point = get_point_for_ip("174.16.202.210")
    assert point is not None
    assert point.lat == location.latitude
    assert point.lon == location.longitude
    assert point.country_code == "US"
    assert point.state_code == "CO"
