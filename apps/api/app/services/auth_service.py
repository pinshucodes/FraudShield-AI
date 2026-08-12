from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictError, UnauthorizedError
from app.schemas.auth import TokenResponse
from app.core.config import settings

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    async def register(self, email: str, password: str, full_name: str):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")
        
        hashed = hash_password(password)
        return await self.user_repo.create(
            email=email,
            full_name=full_name,
            hashed_password=hashed
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError(message="Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedError(message="User is inactive")
            
        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Invalid token type")
            
        import uuid
        user_id = uuid.UUID(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError(message="User not found or inactive")
            
        new_access = create_access_token(str(user.id), user.role.value)
        new_refresh = create_refresh_token(str(user.id))
        
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
