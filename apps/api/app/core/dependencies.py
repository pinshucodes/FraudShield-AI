from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Callable

from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.repositories.user_repo import UserRepository
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(message="Token payload invalid")
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedError(message="Invalid user ID format")
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)
    if not user:
        raise UnauthorizedError(message="User not found")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise UnauthorizedError(message="Inactive user")
    return current_user

def require_role(*roles: str) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(message="Insufficient permissions")
        return current_user
    return role_checker
