import pytest
import httpx
import asyncio
import uuid

# APISIX Gateway URL (Assuming nodePort 30080 on localhost)
BASE_URL = "http://localhost:30080"

@pytest.mark.asyncio
async def test_end_to_end_checkout_flow():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Register User
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword"
        
        register_response = await client.post("/auth/register", json={
            "email": unique_email,
            "password": password
        })
        assert register_response.status_code == 200
        user_id = register_response.json()["id"]

        # 2. Login User
        login_response = await client.post("/auth/token", data={
            "username": unique_email,
            "password": password
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Seed Catalog
        catalog_response = await client.post("/catalog/products", json={
            "name": "Gaming Mouse",
            "description": "High DPI",
            "price": 59.99,
            "stock": 10
        }, headers=headers)
        assert catalog_response.status_code == 201
        product_id = catalog_response.json()["id"]

        # 4. Place Order (Saga Initiated)
        order_response = await client.post("/orders/orders", json={
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 2
        }, headers=headers)
        assert order_response.status_code == 201
        order_data = order_response.json()
        order_id = order_data["id"]
        assert order_data["status"] == "PENDING"

        # 5. Wait for Saga to complete
        max_retries = 10
        order_confirmed = False
        for _ in range(max_retries):
            await asyncio.sleep(2)
            get_order_response = await client.get(f"/orders/orders/{order_id}", headers=headers)
            assert get_order_response.status_code == 200
            status = get_order_response.json()["status"]
            if status == "CONFIRMED":
                order_confirmed = True
                break
                
        assert order_confirmed, "Saga failed to transition order status to CONFIRMED"
