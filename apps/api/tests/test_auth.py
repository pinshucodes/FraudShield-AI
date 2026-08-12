import pytest
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_register_success(test_client: AsyncClient):
    response = await test_client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "full_name": "New User"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True

async def test_register_duplicate_email(test_client: AsyncClient, test_user: User):
    response = await test_client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": "password123",
        "full_name": "Dup"
    })
    assert response.status_code == 409

async def test_login_success(test_client: AsyncClient, test_user: User):
    response = await test_client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data

async def test_login_wrong_password(test_client: AsyncClient, test_user: User):
    response = await test_client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "wrong"
    })
    assert response.status_code == 401

async def test_get_me_authenticated(test_client: AsyncClient, test_user: User):
    login = await test_client.post("/api/v1/auth/login", json={"email": test_user.email, "password": "password123"})
    token = login.json()["data"]["access_token"]
    
    response = await test_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["email"] == test_user.email
