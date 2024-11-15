from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def add_middleware(app: FastAPI):
    # even in development, some sort of CORS is required
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
