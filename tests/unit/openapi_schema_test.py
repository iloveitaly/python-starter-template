from collections import Counter

from app.server import api_app


def test_openapi_operation_ids_are_unique():
    schema = api_app.openapi()
    operation_ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if "operationId" in operation
    ]
    operation_id_counts = Counter(operation_ids)
    duplicate_operation_ids = {
        operation_id for operation_id, count in operation_id_counts.items() if count > 1
    }

    assert not duplicate_operation_ids


def test_colliding_openapi_operation_ids_include_all_route_details():
    schema = api_app.openapi()

    assert (
        schema["paths"]["/internal/v1/ping"]["get"]["operationId"]
        == "external_api_ping_internal_v1_ping_get"
    )
    assert (
        schema["paths"]["/external/v1/ping"]["get"]["operationId"]
        == "external_api_ping_external_v1_ping_get"
    )
