from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=APIResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    user = await service.register(request.email, request.password, request.full_name)
    return APIResponse(message="User registered successfully", data=UserResponse.model_validate(user))

@router.post("/login", response_model=APIResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    tokens = await service.login(request.email, request.password)
    return APIResponse(data=tokens)

@router.post("/refresh", response_model=APIResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    tokens = await service.refresh_token(request.refresh_token)
    return APIResponse(data=tokens)

@router.post("/logout", response_model=APIResponse)
async def logout():
    return APIResponse(message="Logged out successfully")

@router.get("/me", response_model=APIResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse(data=UserResponse.model_validate(current_user))
