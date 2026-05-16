from i18naddress import InvalidAddress, format_address, normalize_address
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, computed_field


class Address(PydanticBaseModel):
    address1: str | None = None
    "address1 of the practice"

    address2: str | None = None
    "address2 of the practice"

    city: str | None = None
    "city of the practice"

    state: str | None = None
    "state of the practice"

    state_code: str | None = Field(default=None, min_length=2, max_length=2)
    "2-letter state code of the practice"

    postal_code: str | None = None
    "postal code of the practice"

    @computed_field
    @property
    def formatted_address(self) -> str | None:
        """
        Dynamically calculates the formatted address using US postal standards.
        Included automatically in model serialization (.model_dump()).
        """
        # If the address is completely empty, return None
        if not any(
            [self.address1, self.city, self.state, self.state_code, self.postal_code]
        ):
            return None

        # Combine street lines for the formatter
        address_lines = [line for line in [self.address1, self.address2] if line]
        street_address = "\n".join(address_lines) if address_lines else ""

        # Let the library apply US postal formatting rules
        formatted = format_address(
            {
                "country_code": "US",
                "country_area": self.state_code or self.state or "",
                "city": self.city or "",
                "postal_code": self.postal_code or "",
                "street_address": street_address,
            }
        )

        # Replace newlines with commas for a clean, single-line string
        return formatted.replace("\n", ", ") if formatted else None

    def validate_address(self) -> Address:
        """
        Manually validates that the address is complete and well-structured
        using strict US formatting rules. Must be explicitly called.
        """
        country_area = self.state_code or self.state

        try:
            address_lines = [line for line in [self.address1, self.address2] if line]

            # normalize_address naturally enforces completeness for US addresses.
            # If city, state, zip, or street are missing/invalid, this will fail.
            clean_address = normalize_address(
                address_lines=address_lines,
                city=self.city,
                country_area=country_area,
                postal_code=self.postal_code,
                country_code="US",
            )

            # Normalize the user's input based on the library's corrections
            if self.postal_code:
                self.postal_code = clean_address.get("postal_code")

        except InvalidAddress as e:
            # e.errors provides a dict of exactly what is missing or invalid
            raise ValueError(f"Incomplete or invalid US address: {e.errors}")

        return self
