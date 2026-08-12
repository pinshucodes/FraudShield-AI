from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from app.schemas.common import PaginatedResponse

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None

class AdminUserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None

class UserListResponse(PaginatedResponse[UserResponse]):
    pass
