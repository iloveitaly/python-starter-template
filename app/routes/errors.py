"""
Custom exceptions for the web application.
"""

import typing as t

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import log

import sqlalchemy.exc

LogLevel = t.Literal["debug", "info", "warning", "error", "critical"]


class ErrorDetail(BaseModel):
    """Standard error payload returned to clients.

    Shape loosely follows Stripe: machine-readable `code`, human-readable
    `message`, optional `param` pointing at the offending field, and an
    optional `details` bag for structured context.
    """

    code: str
    message: str
    param: str | None = None
    details: dict[str, t.Any] | None = None


class ErrorResponse(BaseModel):
    """Envelope wrapping `ErrorDetail` under an `error` key.

    The wrapper gives error responses a stable shape (`{"error": {...}}`)
    that clients can discriminate on, and leaves room to add sibling
    top-level fields later (e.g., `request_id`, `meta`) without a
    breaking change.
    """

    error: ErrorDetail


class ClientError(Exception):
    """Expected client or business logic errors (HTTP 4xx).

    Raised when a request is invalid due to client input or business rule
    violations. The contents of `message`, `code`, `param`, and `details` are
    safe to expose to the end user. `internal_details` is logged only.

    Args:
        message: Human-readable error message explaining what went wrong.
            Positional because it is the semantic payload callers think about
            first.
        status_code: HTTP status code to return. Must be in the 4xx range;
            enforced by assertion.
        code: Machine-readable string code for frontend handling
            (e.g., "INSUFFICIENT_FUNDS", "USER_NOT_FOUND"). Required - no
            generic fallback, since a default code is worse than no code:
            present enough to look meaningful, vague enough to be ignored.
        param: Specific field or query parameter that caused the error
            (e.g., "email", "user_id"). Defaults to None.
        details: Additional structured data providing context about the error.
            Exposed to the client. Defaults to None and is omitted from the
            response when not set.
        internal_details: Structured data to attach to the log record but
            never surface to the client. Use for things like internal IDs,
            upstream response bodies, or anything sensitive that aids
            debugging. Defaults to None.
        level: Log level to emit when this error is raised. Defaults to
            "info" since these are expected, in-spec errors. Bump to
            "warning" or "error" for cases that suggest client/server
            contract drift or genuinely unexpected business-rule misses.

    Raises:
        AssertionError: If status_code is not in the 4xx range.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        param: str | None = None,
        details: dict[str, t.Any] | None = None,
        internal_details: dict[str, t.Any] | None = None,
        level: LogLevel = "info",
    ):
        assert 400 <= status_code < 500, (
            f"ClientError status_code must be 4xx, got {status_code}"
        )

        self.message = message
        self.status_code = status_code
        self.code = code
        self.param = param
        self.details = details
        self.internal_details = internal_details
        self.level = level

        super().__init__(self.message)


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

    @app.exception_handler(sqlalchemy.exc.NoResultFound)
    async def sqlalchemy_no_result_handler(request, exc: Exception):
        """
        Most of the time a 404 is the intended response, but if more complex logic is executed, this exception
        could be unintentionally raised.

        We are going to take a risk and log and return a 404, *without* logging to sentry.
        """

        assert isinstance(exc, sqlalchemy.exc.NoResultFound)

        # TODO looks like the model and requested ID are NOT attached to the error, which is a bummer :/
        # TODO I should inspect the error logs for this, it really should contain the request ID
        log.info("NoResultFound transformed by fastapi")
        log.debug("NoResultFound traceback", exc_info=exc)

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="Resource not found.",
                )
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Format request validation errors (pydantic validation errors) using the standard ErrorResponse shape.

        Pydantic's structured errors are passed through in `details.errors` so
        frontends can map failures to specific fields without parsing strings.
        `jsonable_encoder` strips non-serializable objects that pydantic v2
        sometimes embeds in error context.

        Lifted from https://github.com/fastapi/fastapi/issues/3361
        """
        errors = jsonable_encoder(exc.errors())

        # with the fastapi access logger in place, this contains the request ID so it can be correlated with a request
        log.info(
            "validation_error",
            code="VALIDATION_ERROR",
            error_count=len(errors),
            errors=errors,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="Request validation failed.",
                    details={"errors": errors},
                )
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(ClientError)
    async def app_client_error_handler(
        request: Request, exc: ClientError
    ) -> JSONResponse:
        """
        Catch ClientError and format it as a standardized JSON response.

        Emits a log at the level configured on the exception so
        client errors are queryable. `internal_details` is included in the log but
        deliberately omitted from the response payload.

        structlog_config will include the request ID, if it exists on the starlette context.
        """

        log_func = getattr(log, exc.level)
        log_func(
            "client_error",
            code=exc.code,
            status_code=exc.status_code,
            param=exc.param,
            details=exc.details,
            internal_details=exc.internal_details,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    param=exc.param,
                    details=exc.details,
                )
            ).model_dump(exclude_none=True),
        )
