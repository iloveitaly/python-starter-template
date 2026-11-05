import usaddress
from funcy import project


def parse_address(input_str: str) -> dict[str, str]:
    """
    Surprisingly, all of the APIs out there for this sort of thing are obnoxious and this library seems to work well
    for taking an address string and breaking it into components, and then combining those components into the
    fields we want.
    """

    parsed, _ = usaddress.tag(input_str)

    addr_keys = [
        "AddressNumber",
        "StreetNamePreDirectional",
        "StreetName",
        "StreetNamePostType",
        "StreetNamePostDirectional",
        "OccupancyType",
        "OccupancyIdentifier",
    ]
    address1 = " ".join(project(parsed, addr_keys).values()).strip()

    return {
        "address1": address1,
        "postalCode": parsed.get("ZipCode", ""),
        "city": parsed.get("PlaceName", ""),
        "state": parsed.get("StateName", ""),
    }
