import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.response import error


logger = logging.getLogger(__name__)


class AppException(Exception):
    """
    Custom business exception for application-level errors.
    """

    def __init__(self, message: str = "application error", code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException occurred: %s", exc.message)
    return JSONResponse(
        status_code=200,
        content=error(message=exc.message, code=exc.code).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=error(message="validation error", code=422, data=exc.errors()).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content=error(message="internal server error", code=500).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)