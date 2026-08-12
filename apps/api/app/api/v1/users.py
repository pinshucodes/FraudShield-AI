from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.schemas.user import UserResponse, UserUpdateRequest, AdminUserUpdateRequest, UserListResponse
from app.schemas.common import APIResponse, PaginationParams
from app.services.user_service import UserService
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter()

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))

@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
async def list_users(params: PaginationParams = Depends(), service: UserService = Depends(get_user_service)):
    return await service.list_users(params.page, params.page_size)

@router.get("/{user_id}", response_model=APIResponse)
async def get_user(user_id: UUID, current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    from app.core.exceptions import ForbiddenError
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise ForbiddenError("Not allowed")
    user = await service.get_user(user_id)
    return APIResponse(data=UserResponse.model_validate(user))

@router.put("/me", response_model=APIResponse)
async def update_me(request: UserUpdateRequest, current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    user = await service.update_user(current_user.id, request.model_dump(exclude_unset=True))
    return APIResponse(data=UserResponse.model_validate(user))

@router.put("/{user_id}/role", response_model=APIResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_role(user_id: UUID, request: AdminUserUpdateRequest, service: UserService = Depends(get_user_service)):
    user = await service.update_user_role(user_id, request.role)
    return APIResponse(data=UserResponse.model_validate(user))

@router.delete("/{user_id}", response_model=APIResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    await service.user_repo.soft_delete(user_id)
    return APIResponse(message="User deleted")
