from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.setup import get_root_path


def mount_public_directory(app: FastAPI):
    app.mount(
        "/public",
        StaticFiles(directory=get_root_path() / "public", html=True),
        name="public",
    )
