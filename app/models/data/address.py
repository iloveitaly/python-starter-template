from typing import Any, Self

import us
from i18naddress import InvalidAddress, format_address, normalize_address
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class Address(BaseModel):
    """
    US postal address with flexible state input and derived state name.

    State input
    -----------
    The canonical stored field is `state_code` (two-letter, uppercase). For
    convenience, callers may pass `state=` at construction with any form the
    `us` package recognizes:

        Address(state="Colorado")    # full name
        Address(state="colorado")    # case-insensitive
        Address(state="CO")          # 2-letter code
        Address(state="Colo.")       # AP-style abbreviation
        Address(state_code="co")     # also works; gets uppercased

    All of the above yield `state_code="CO"` and `state="Colorado"`.

    Precedence: if both `state` and `state_code` are provided, `state_code`
    wins and `state` is discarded. Unknown state input raises `ValueError`
    at construction.

    Computed fields
    ---------------
    `state` (full name) and `formatted_address` are computed from
    `state_code` and the other stored fields. Both appear in `model_dump()`
    output. `Address(**addr.model_dump())` round-trips correctly: the
    pre-validator drops the incoming `state` because `state_code` is
    already set.

    Validation vs. normalization
    ----------------------------
    Construction only validates the state token; it does NOT require a
    complete address. Call `normalized()` to enforce US postal completeness
    (street, city, state, ZIP) and to receive a new instance with library-
    corrected fields. The original instance is never mutated.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_attribute_docstrings=True,
    )

    address1: str | None = None
    """First street line."""

    address2: str | None = None
    """Second street line (suite, apt, etc.)."""

    city: str | None = None
    """City."""

    state_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    """Two-letter US state code. Also settable via `state=` (see class docstring)."""

    postal_code: str | None = None
    """ZIP or ZIP+4."""

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

        match = us.states.lookup(state_in.strip())
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
        match = us.states.lookup(self.state_code)
        return match.name if match else None

    def _as_i18n_dict(self) -> dict[str, str]:
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
        if not any((self.address1, self.city, self.state_code, self.postal_code)):
            return None
        formatted = format_address(self._as_i18n_dict())
        return formatted.replace("\n", ", ") if formatted else None

    def normalized(self) -> Self:
        """
        Return a new `Address` with library-corrected fields (uppercased
        state, hyphenated ZIP+4, etc.). Does not mutate self.

        Raises `ValueError` if the address is incomplete or invalid per US
        postal rules — i.e. missing street, city, state, or ZIP, or a ZIP
        that does not match the state.
        """
        try:
            clean = normalize_address(self._as_i18n_dict())
        except InvalidAddress as e:
            raise ValueError(f"Incomplete or invalid US address: {e.errors}") from e

        street_lines = (clean.get("street_address") or "").splitlines()
        return self.model_copy(
            update={
                "address1": street_lines[0] if street_lines else self.address1,
                "address2": street_lines[1] if len(street_lines) > 1 else self.address2,
                "city": clean.get("city") or self.city,
                "state_code": clean.get("country_area") or self.state_code,
                "postal_code": clean.get("postal_code") or self.postal_code,
            }
        )
