import pytest
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_list_users_admin(test_client: AsyncClient, test_admin: User):
    login = await test_client.post("/api/v1/auth/login", json={"email": test_admin.email, "password": "password123"})
    token = login.json()["data"]["access_token"]
    
    response = await test_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

async def test_list_users_non_admin_forbidden(test_client: AsyncClient, test_user: User):
    login = await test_client.post("/api/v1/auth/login", json={"email": test_user.email, "password": "password123"})
    token = login.json()["data"]["access_token"]
    
    response = await test_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
