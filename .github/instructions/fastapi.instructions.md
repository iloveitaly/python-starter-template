---
applyTo: "app/routes/**/*.py"
---
## FastAPI

- When throwing a `HTTPException`, do not add a `detail=` and use a named status code (`status.HTTP_400_BAD_REQUEST`)
- Do not return a `dict`, instead create a `class RouteNameResponse`
  - Locate these classes right above the `def route_name():` function which uses them.
- Use `Model.one` when a record must exist in order for the business logic to succeed.
- Do not try/except `Model.one` when using a parameter from the request to pull a record. Let this exception bubble up.
- Use `model_id: Annotated[TypeIDType, Path()]` to represent a model ID as a URL path parameter
