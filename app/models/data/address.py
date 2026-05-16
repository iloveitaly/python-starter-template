from typing import Any, Self

import us
from i18naddress import InvalidAddressError, format_address, normalize_address
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.utils.address import parse_address


class Address(BaseModel):
    """US postal address with flexible state input and derived state name.

    **State input:** The canonical stored field is `state_code` (two-letter,
    uppercase). Callers may pass `state=` at construction with any form the
    `us` package recognizes:

        Address(state="Colorado")   # full name
        Address(state="colorado")   # case-insensitive
        Address(state="CO")         # 2-letter code
        Address(state_code="co")    # also works; gets uppercased

    If both `state` and `state_code` are provided, `state_code` wins and
    `state` is discarded. Unknown state input raises `ValueError`.

    **Computed fields:** `state` (full name) and `formatted_address` are
    derived from `state_code` and the other stored fields. Both appear in
    `model_dump()` output. `Address(**addr.model_dump())` round-trips
    correctly because the pre-validator drops the incoming `state` when
    `state_code` is already set.

    **Normalization:** Construction only validates the state token; it does
    NOT require a complete address. Call `normalized()` to enforce US postal
    completeness and receive a new instance with library-corrected fields.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_attribute_docstrings=True,
    )

    address1: str | None = None
    "First street line."

    address2: str | None = None
    "Second street line (suite, apt, etc.)."

    city: str | None = None
    "City."

    state_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    "Two-letter US state code. Also settable via `state=` (see class docstring)."

    postal_code: str | None = None
    "ZIP or ZIP+4."

    @classmethod
    def from_string(cls, address_str: str) -> Self:
        """Parse a free-form US address string into an `Address`.

        Args:
            address_str: Free-form US address string, e.g. `"123 Main St, Denver, CO 80203"`.
        """
        parsed = parse_address(address_str)
        # use `state=` (not `state_code=`) so the value passes through _resolve_state
        return cls.model_validate(
            {
                "address1": parsed.get("address1") or None,
                "city": parsed.get("city") or None,
                "state": parsed.get("state") or None,
                "postal_code": parsed.get("postalCode") or None,
            }
        )

    @model_validator(mode="before")
    @classmethod
    def _resolve_state(cls, data: Any) -> Any:
        """
        Resolve a `state` input (full name, code, or AP abbreviation) into
        `state_code`. If `state_code` is already present, it wins and any
        `state` value is dropped — this is what makes `model_dump()` round-
        tripping safe, since dumps include both fields.
        """
        if not isinstance(data, dict):
            return data

        state_in = data.pop("state", None)

        if data.get("state_code"):
            data["state_code"] = data["state_code"].strip().upper()
            return data

        if not state_in:
            return data

        normalized = state_in.strip()
        # us.states.lookup covers the 50 states + territories but not DC;
        # fall back to a direct module attribute for two-letter codes (e.g. "DC")
        match = us.states.lookup(normalized) or getattr(us.states, normalized.upper(), None)
        if match is None:
            raise ValueError(f"Unknown US state: {state_in!r}")
        data["state_code"] = match.abbr
        return data

    @computed_field
    @property
    def state(self) -> str | None:
        """Full state name derived from `state_code` (e.g. 'Colorado')."""
        if not self.state_code:
            return None
        match = us.states.lookup(self.state_code) or getattr(us.states, self.state_code, None)
        return match.name if match else None

    def _as_i18n_dict(self) -> dict[str, str]:
        # i18naddress uses its own field names: country_area=state, street_address=combined lines
        return {
            "country_code": "US",
            "country_area": self.state_code or "",
            "city": self.city or "",
            "postal_code": self.postal_code or "",
            "street_address": "\n".join(filter(None, (self.address1, self.address2))),
        }

    @computed_field
    @property
    def formatted_address(self) -> str | None:
        """
        Single-line, US-formatted address, or None if the address is empty.
        Recomputed on every access (and every `model_dump()`).
        """

        # no fields are strictly required, so we need to check that *something* exists
        if not any((self.address1, self.city, self.state_code, self.postal_code)):
            return None

        # format_address returns a newline-separated string; flatten to a single line
        formatted = format_address(self._as_i18n_dict())
        return formatted.replace("\n", ", ") if formatted else None

    def validate_address(self) -> list[dict[str, Any]]:
        """Return a list of pydantic-style error dicts for any postal-completeness
        issues. Empty list means the address passes US postal validation."""

        # maps i18naddress field names (from InvalidAddressError.errors) back to our model field names
        field_map = {
            "street_address": "address1",
            "city": "city",
            "country_area": "state_code",
            "postal_code": "postal_code",
        }

        # normalize_address raises InvalidAddressError if any required field is missing or inconsistent
        try:
            normalize_address(self._as_i18n_dict())
        except InvalidAddressError as e:
            errors = []
            for i18n_field, reason in e.errors.items():
                our_field = field_map.get(i18n_field) or i18n_field
                errors.append({
                    "type": reason,
                    "loc": (our_field,),
                    "msg": reason,
                    "input": getattr(self, our_field, None),
                })
            return errors

        return []

    def normalized(self) -> Self:
        """Return a new `Address` with library-corrected fields. Does not mutate self.

        Raises:
            ValueError: If the address is incomplete or invalid per US postal
                rules (missing street, city, state, or ZIP, or a ZIP that does
                not match the state).
        """
        try:
            clean = normalize_address(self._as_i18n_dict())
        except InvalidAddressError as e:
            raise ValueError(f"Incomplete or invalid US address: {e.errors}") from e

        # normalize_address may correct capitalization, expand abbreviations, etc.
        street_lines = (clean.get("street_address") or "").splitlines()
        # model_copy(update=...) returns a new instance with only the specified fields replaced
        return self.model_copy(
            update={
                "address1": street_lines[0] if street_lines else self.address1,
                "address2": street_lines[1] if len(street_lines) > 1 else self.address2,
                "city": clean.get("city") or self.city,
                "state_code": clean.get("country_area") or self.state_code,
                "postal_code": clean.get("postal_code") or self.postal_code,
            }
        )
