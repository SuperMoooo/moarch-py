"""The errors services raise, and the one handler that turns them into HTTP responses.

Services never import FastAPI. They raise an `AppError` that names what went
wrong in the product's terms; `register_error_handlers` maps it to a status
code and a JSON body with the same shape for every error.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base for every error the API reports on purpose."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """The requested resource does not exist (or the caller may not know it does)."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    """The request clashes with existing data, such as a duplicate unique value."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class PermissionDeniedError(AppError):
    """The caller is known but not allowed to do this."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


async def _app_error_handler(_: Request, error: Exception) -> JSONResponse:
    # Starlette types handlers as taking any Exception; this one is registered
    # for AppError only, so the assert never fails and only narrows the type.
    assert isinstance(error, AppError)
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Makes every `AppError` raised anywhere answer as `{"error": {code, message}}`."""
    app.add_exception_handler(AppError, _app_error_handler)
