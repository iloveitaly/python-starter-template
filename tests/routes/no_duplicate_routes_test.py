from collections import Counter

from app.server import api_app


def test_no_duplicate_route_names():
    """
    Ensure all route names in the FastAPI application are unique.

    This test collects route names from the app's routes, checks for duplicates,
    and raises an AssertionError if any are found.
    """
    # Extract route names, filtering out routes without names
    route_names = [
        route.name for route in api_app.routes if hasattr(route, "name") and route.name
    ]

    # Identify duplicates using Counter
    name_counts = Counter(route_names)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}

    # Assert no duplicates exist
    assert not duplicates, f"Duplicate route names found: {duplicates}"
