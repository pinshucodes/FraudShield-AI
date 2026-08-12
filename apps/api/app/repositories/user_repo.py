from app.repositories.base import BaseRepository
from app.models.user import User, UserRole
from sqlalchemy import select, func
import uuid
from typing import Tuple, List

class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)
        
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).filter_by(email=email, deleted_at=None))
        return result.scalars().first()

    async def get_active_users(self, skip: int, limit: int) -> Tuple[List[User], int]:
        query = select(User).filter_by(is_active=True, deleted_at=None)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def update_role(self, user_id: uuid.UUID, role: UserRole) -> User | None:
        return await self.update(user_id, role=role)
