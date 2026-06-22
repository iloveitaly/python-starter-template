"""
Very simple model to represent a point and some metadata associated with the point.

We could use GeoJSON, and it probably makes sense to write some bindings at some point, but in many geolocation
use cases you just need a very simple unopinionated point object. That's what this is.
"""

from typing import Any

from apple_maps_api import Place
from pydantic import BaseModel as PydanticBaseModel
from pydantic import model_validator
from radar_mapping_api import Address


class GeolocationPoint(PydanticBaseModel):
    lat: float
    lon: float

    address1: str | None = None
    address2: str | None = None

    city: str | None = None
    postal_code: str | None = None

    state: str | None = None
    state_code: str | None = None

    country: str | None = None
    country_code: str | None = None

    @classmethod
    def from_tuple(cls, tuple: tuple[float, float]) -> GeolocationPoint:
        return cls(
            lat=tuple[1],
            lon=tuple[0],
        )

    @model_validator(mode="after")
    def validate_coordinates(self) -> GeolocationPoint:
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError("Latitude must be within [-90, 90]")
        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError("Longitude must be within [-180, 180]")
        return self

    @model_validator(mode="before")
    @classmethod
    def convert_tuple(cls, data: Any) -> dict | Any:
        if isinstance(data, tuple) and len(data) == 2:
            return {
                "lat": data[1],
                "lon": data[0],
            }
        return data

    @classmethod
    def from_radar_address(cls, address: Address) -> GeolocationPoint:
        address_line_1 = (
            f"{address.number} {address.street}"
            if address.number and address.street
            else None
        )
        # TODO: 'Address' object doesn't provide
        # a clear way to get an address line 2
        address_line_2 = None

        return cls(
            lat=address.latitude,
            lon=address.longitude,
            address1=address_line_1,
            address2=address_line_2,
            city=address.city,
            postal_code=address.postalCode,
            state=address.state,
            state_code=address.stateCode,
            country=address.country,
            country_code=address.countryCode,
        )

    @classmethod
    def from_apple_maps_place(cls, place: Place) -> GeolocationPoint:
        sa = place.structuredAddress
        return cls(
            lat=place.coordinate.latitude if place.coordinate else 0.0,
            lon=place.coordinate.longitude if place.coordinate else 0.0,
            address1=sa.fullThoroughfare if sa else None,
            address2=None,
            city=sa.locality if sa else None,
            postal_code=sa.postCode if sa else None,
            state=sa.administrativeArea if sa else None,
            state_code=sa.administrativeAreaCode if sa else None,
            country=place.country,
            country_code=place.countryCode,
        )
