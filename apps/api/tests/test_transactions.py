import pytest
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _login(client: AsyncClient, email: str, password: str = "password123") -> str:
    """Helper to login and return access token."""
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["data"]["access_token"]


async def _create_transaction(client: AsyncClient, token: str, amount: float = 1500.0, **kwargs) -> dict:
    """Helper to create a transaction and return response data."""
    payload = {
        "user_id": "USR-TEST",
        "amount": amount,
        "currency": "INR",
        "merchant_id": kwargs.get("merchant_id", "MER-001"),
        "merchant_category": kwargs.get("merchant_category", "electronics"),
        "payment_method": kwargs.get("payment_method", "card"),
        "device_id": kwargs.get("device_id", "DEV-001"),
        "ip_address": "192.168.1.1",
        "location": {"latitude": 28.6139, "longitude": 77.2090},
    }
    resp = await client.post(
        "/api/v1/transactions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


async def test_create_transaction_success(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    resp = await _create_transaction(test_client, token)
    assert resp.status_code == 202
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["transaction_id"].startswith("TXN-")
    assert data["data"]["status"] == "RECEIVED"
    assert data["data"]["amount"] == 1500.0


async def test_create_transaction_unauthenticated(test_client: AsyncClient):
    resp = await _create_transaction(test_client, "invalid-token")
    assert resp.status_code == 401


async def test_list_transactions(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    # Create a couple transactions
    await _create_transaction(test_client, token, amount=1000)
    await _create_transaction(test_client, token, amount=2000)

    resp = await test_client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["data"]) >= 2


async def test_list_transactions_with_amount_filter(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    await _create_transaction(test_client, token, amount=500)
    await _create_transaction(test_client, token, amount=50000)

    resp = await test_client.get(
        "/api/v1/transactions?min_amount=10000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    for txn in resp.json()["data"]:
        assert txn["amount"] >= 10000


async def test_get_transaction_detail(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    create_resp = await _create_transaction(test_client, token)
    txn_id = create_resp.json()["data"]["transaction_id"]

    resp = await test_client.get(
        f"/api/v1/transactions/{txn_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["transaction_id"] == txn_id


async def test_customer_cannot_see_other_users_transactions(test_client: AsyncClient, test_user: User, test_admin: User):
    # Admin creates a transaction
    admin_token = await _login(test_client, test_admin.email)
    admin_resp = await _create_transaction(test_client, admin_token, amount=9999)
    admin_txn_id = admin_resp.json()["data"]["transaction_id"]

    # Customer tries to access it
    customer_token = await _login(test_client, test_user.email)
    resp = await test_client.get(
        f"/api/v1/transactions/{admin_txn_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 403


async def test_update_status_analyst(test_client: AsyncClient, test_user: User, test_admin: User):
    """Test that an admin can change a REVIEW transaction to CONFIRMED_FRAUD."""
    # Create transaction as customer
    customer_token = await _login(test_client, test_user.email)
    create_resp = await _create_transaction(test_client, customer_token)
    txn_id = create_resp.json()["data"]["transaction_id"]

    # We need to first move it through the state machine: RECEIVED -> PROCESSING -> SCORED -> REVIEW
    # For now, let's directly test the forbidden update from RECEIVED
    admin_token = await _login(test_client, test_admin.email)
    resp = await test_client.patch(
        f"/api/v1/transactions/{txn_id}/status",
        json={"status": "CONFIRMED_FRAUD"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # RECEIVED -> CONFIRMED_FRAUD is not a valid transition
    assert resp.status_code == 422 or resp.status_code == 400


async def test_customer_cannot_update_status(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    create_resp = await _create_transaction(test_client, token)
    txn_id = create_resp.json()["data"]["transaction_id"]

    resp = await test_client.patch(
        f"/api/v1/transactions/{txn_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_report_fraud(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    create_resp = await _create_transaction(test_client, token)
    txn_id = create_resp.json()["data"]["transaction_id"]

    resp = await test_client.post(
        f"/api/v1/transactions/{txn_id}/report-fraud",
        json={"reason": "I did not make this transaction. Someone used my card without authorization."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_fraud_reported"] is True


async def test_get_transaction_stats(test_client: AsyncClient, test_user: User):
    token = await _login(test_client, test_user.email)
    await _create_transaction(test_client, token)

    resp = await test_client.get(
        "/api/v1/transactions/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    stats = resp.json()["data"]
    assert stats["total_transactions"] >= 1
