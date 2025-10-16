"""
Very simple model to represent a point and some metadata associated with the point.

We could use GeoJSON, and it probably makes sense to write some bindings at some point, but in many geolocation
use cases you just need a very simple unopinionated point object. That's what this is.
"""

from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import model_validator


class GeolocationPoint(PydanticBaseModel):
    lat: float
    lng: float

    city: str | None = None
    postal_code: str | None = None
    state: str | None = None

    @classmethod
    def from_tuple(cls, tuple: tuple[float, float]) -> "GeolocationPoint":
        return cls(
            lat=tuple[1],
            lon=tuple[0],
        )

    @model_validator(mode="after")
    def validate_coordinates(self) -> "GeolocationPoint":
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
