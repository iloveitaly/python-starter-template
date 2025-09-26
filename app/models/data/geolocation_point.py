"""
Very simple model to represent a point and some metadata associated with the point.

We could use GeoJSON, and it probably makes sense to write some bindings at some point, but in many geolocation
use cases you just need a very simple unopinionated point object. That's what this is.
"""

from pydantic import BaseModel as PydanticBaseModel


class GeolocationPoint(PydanticBaseModel):
    lat: float
    lng: float

    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
