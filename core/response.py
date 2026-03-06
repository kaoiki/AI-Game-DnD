from typing import Any

from schemas.base import ApiResponse


def success(data: Any = None, message: str = "success", code: int = 0) -> ApiResponse:
    return ApiResponse(
        code=code,
        message=message,
        data=data,
    )


def error(message: str = "error", code: int = 1, data: Any = None) -> ApiResponse:
    return ApiResponse(
        code=code,
        message=message,
        data=data,
    )