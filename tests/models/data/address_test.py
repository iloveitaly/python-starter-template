import pytest
from pydantic import ValidationError

from app.models.data.address import Address

VALID_ADDRESS = {
    "address1": "200 E Colfax Ave",
    "city": "Denver",
    "state_code": "CO",
    "postal_code": "80203",
}


####################
# State resolution
####################


@pytest.mark.parametrize(
    "state_in, expected_code, expected_name",
    [
        ("Colorado", "CO", "Colorado"),
        ("colorado", "CO", "Colorado"),
        ("CO", "CO", "Colorado"),
    ],
)
def test_state_input_forms(state_in, expected_code, expected_name):
    addr = Address.model_validate({"state": state_in})

    assert addr.state_code == expected_code
    assert addr.state == expected_name


def test_state_code_lowercase_is_uppercased():
    addr = Address(state_code="co")

    assert addr.state_code == "CO"


def test_state_code_wins_over_state():
    # state_code takes precedence; state="California" is discarded
    addr = Address.model_validate({"state": "California", "state_code": "CO"})

    assert addr.state_code == "CO"
    assert addr.state == "Colorado"


def test_unknown_state_raises():
    with pytest.raises(ValueError, match="Unknown US state"):
        Address.model_validate({"state": "Atlantis"})


def test_invalid_state_code_pattern_raises():
    with pytest.raises(ValidationError):
        Address(state_code="CALIF")


def test_no_state_inputs_yields_none():
    addr = Address()

    assert addr.state_code is None
    assert addr.state is None


#####################
# formatted_address
#####################


def test_formatted_address_none_when_empty():
    assert Address().formatted_address is None


def test_formatted_address_is_single_line():
    addr = Address(**VALID_ADDRESS)
    result = addr.formatted_address

    assert result is not None
    assert "\n" not in result


def test_formatted_address_partial_city_and_state():
    addr = Address(city="Denver", state_code="CO")

    assert addr.formatted_address is not None


######################
# model_dump round-trip
######################


def test_model_dump_includes_computed_fields():
    addr = Address(**VALID_ADDRESS)
    dump = addr.model_dump()

    assert "state" in dump
    assert "formatted_address" in dump


def test_round_trip_via_model_dump():
    addr = Address(**VALID_ADDRESS)
    restored = Address(**addr.model_dump())

    assert restored.state_code == addr.state_code
    assert restored.state == addr.state
    assert restored.formatted_address == addr.formatted_address


################
# normalized()
################


def test_normalized_returns_new_instance():
    addr = Address(**VALID_ADDRESS)
    normalized = addr.normalized()

    assert normalized is not addr
    assert addr.address1 == VALID_ADDRESS["address1"]


def test_normalized_uppercases_city():
    addr = Address(**VALID_ADDRESS)
    normalized = addr.normalized()

    # i18naddress normalizes city to uppercase
    assert normalized.city == "DENVER"


def test_normalized_preserves_zip_plus_four():
    addr = Address(**{**VALID_ADDRESS, "postal_code": "80203-1234"})
    normalized = addr.normalized()

    assert normalized.postal_code == "80203-1234"


def test_normalized_two_line_street_preserved():
    addr = Address(
        **{**VALID_ADDRESS, "address1": "200 E Colfax Ave", "address2": "Suite 100"}
    )
    normalized = addr.normalized()

    assert normalized.address1 == "200 E Colfax Ave"
    assert normalized.address2 == "Suite 100"


def test_normalized_missing_street_raises():
    addr = Address(city="Denver", state_code="CO", postal_code="80203")

    with pytest.raises(ValueError, match="Incomplete or invalid US address"):
        addr.normalized()


def test_normalized_missing_city_raises():
    addr = Address(address1="200 E Colfax Ave", state_code="CO", postal_code="80203")

    with pytest.raises(ValueError, match="Incomplete or invalid US address"):
        addr.normalized()


def test_normalized_missing_postal_code_raises():
    addr = Address(address1="200 E Colfax Ave", city="Denver", state_code="CO")

    with pytest.raises(ValueError, match="Incomplete or invalid US address"):
        addr.normalized()


def test_normalized_zip_state_mismatch_raises():
    # CO zip (80203) does not match CA
    addr = Address(
        address1="200 E Colfax Ave",
        city="Los Angeles",
        state_code="CA",
        postal_code="80203",
    )

    with pytest.raises(ValueError, match="Incomplete or invalid US address"):
        addr.normalized()


###############
# from_string
###############


def test_from_string_full_address():
    addr = Address.from_string("200 E Colfax Ave, Denver, CO 80203")

    assert addr.address1 == "200 E Colfax Ave"
    assert addr.city == "Denver"
    assert addr.state_code == "CO"
    assert addr.postal_code == "80203"


def test_from_string_empty_components_are_none():
    # usaddress returns "" for missing fields; from_string must convert to None
    addr = Address.from_string("Denver, CO")

    assert addr.postal_code is None
    assert addr.address1 is None


def test_from_string_state_resolves_to_code():
    addr = Address.from_string("200 E Colfax Ave, Denver, Colorado 80203")

    assert addr.state_code == "CO"
    assert addr.state == "Colorado"


######################
# Whitespace stripping
######################


def test_whitespace_stripped_on_construction():
    addr = Address(city="  Denver  ", address1="  123 Main St  ")

    assert addr.city == "Denver"
    assert addr.address1 == "123 Main St"
