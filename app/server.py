"""
`fastapi` cli will automatically start a uvicorn server using this file
"""

from fastapi import FastAPI

from app.environments import is_production

fast_api_args = {}

# disable API documentation in production
if is_production():
    fast_api_args = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(**fast_api_args)

# TODO set this up for the static frontend build
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
