from app.repositories.user_repo import UserRepository
from app.core.exceptions import NotFoundError
import uuid

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user(self, user_id: uuid.UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.deleted_at:
            raise NotFoundError("User not found")
        return user

    async def update_user(self, user_id: uuid.UUID, data: dict):
        user = await self.user_repo.update(user_id, **data)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def list_users(self, page: int, page_size: int, filters: dict = None):
        skip = (page - 1) * page_size
        users, total = await self.user_repo.get_all(skip=skip, limit=page_size, filters=filters)
        return {
            "success": True,
            "data": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def update_user_role(self, user_id: uuid.UUID, role: str):
        from app.models.user import UserRole
        return await self.user_repo.update_role(user_id, UserRole(role))

    async def deactivate_user(self, user_id: uuid.UUID):
        return await self.user_repo.update(user_id, is_active=False)
