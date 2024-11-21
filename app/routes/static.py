from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.setup import get_root_path


def mount_public_directory(app: FastAPI):
    public_path = get_root_path() / "public"

    app.mount(
        "/assets",
        StaticFiles(directory=public_path, html=False),
        name="public",
    )

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(public_path / "index.html")

    return app
