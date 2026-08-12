from pydantic import BaseModel, Field
from typing import Any, List, Generic, TypeVar

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Any = None

class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
