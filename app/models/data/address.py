from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class Address(PydanticBaseModel):
    address1: str
    "address1 of the practice"

    address2: str | None = None
    "address2 of the practice"

    city: str
    "city of the practice"

    state: str
    "state of the practice"

    postal_code: str
    "postal code of the practice"
