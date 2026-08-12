import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User, UserRole
from app.core.security import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def test_client():
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def test_user(test_db):
    user = User(
        email="customer@example.com",
        full_name="Test Customer",
        hashed_password=hash_password("password123"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def test_admin(test_db):
    admin = User(
        email="admin@example.com",
        full_name="Test Admin",
        hashed_password=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin
