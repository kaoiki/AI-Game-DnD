from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    code: int = Field(default=0, description="Business status code")
    message: str = Field(default="success", description="Response message")
    data: Any = Field(default=None, description="Response payload")