---
applyTo: "app/routes/**/*.py"
---
## FastAPI

- When throwing a `HTTPException`, do not add a `detail=` and use a named status code (`status.HTTP_400_BAD_REQUEST`)
- Do not return a `dict`, instead create a `class RouteNameResponse`
  - Locate these classes right above the `def route_name():` function which uses them.
