"""
Custom exceptions for the web application.
"""

from fastapi import FastAPI, Request, status
from pydantic import BaseModel

from app import log

from sqlalchemy.exc import NoResultFound


class EarlyResponseException(Exception):
    """
    Throw this exception to stop execution and return a result, but not necessarily an error,

    Helpful for managing control flow.
    """

    def __init__(
        self,
        *,
        data: dict | BaseModel,
        status: int = status.HTTP_200_OK,
    ):
        if isinstance(data, BaseModel):
            self.data = data.model_dump()
        else:
            self.data = data

        self.status = status


def register_exception_handlers(app: FastAPI):
    # control flow

    async def early_response_handler(request: Request, exc: Exception):
        # typing the parameter conflicts with the FastAPI sig below
        assert isinstance(exc, EarlyResponseException)
        return JSONResponse(status_code=exc.status, content=exc.data)

    app.add_exception_handler(EarlyResponseException, early_response_handler)

    # SQLAlchemy transformations

    async def no_result_exception_handler(request, exc: Exception):
        """
        Most of the time a 404 is the intended response, but if more complex logic is executed, this exception
        could be unintentionally raised.

        We are going to take a risk and log and return a 404, *without* logging to sentry.
        """

        assert isinstance(exc, NoResultFound)

        # TODO looks like the model and requested ID are NOT attached to the error, which is a bummer :/
        log.info("NoResultFound transformed by fastapi")
        log.debug("NoResultFound traceback", exc_info=exc)

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Resource not found"},
        )

    app.add_exception_handler(NoResultFound, no_result_exception_handler)

    # https://github.com/fastapi/fastapi/issues/3361

    from fastapi import status
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    # TODO most likely we should turn this off in production? Need to think through this more.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
        log.error(f"validation error {request}: {exc_str}")
        content = {"status_code": 10422, "message": exc_str, "data": None}
        return JSONResponse(
            content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
