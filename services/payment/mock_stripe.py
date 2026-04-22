import time
import json
import hmac
import hashlib
import httpx
import asyncio

WEBHOOK_SECRET = "whsec_mocksecret"
WEBHOOK_URL = "http://localhost:30080/payment/webhook" # Hitting APISIX Gateway

def generate_stripe_signature(payload: str, secret: str) -> str:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload}"
    mac = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={mac}"

async def send_mock_webhook(event_id: str, retry: bool = False):
    payload_dict = {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_mock123",
                "amount": 2000,
                "currency": "usd"
            }
        }
    }
    payload_str = json.dumps(payload_dict)
    signature = generate_stripe_signature(payload_str, WEBHOOK_SECRET)
    
    headers = {
        "Stripe-Signature": signature,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print(f"Sending webhook event {event_id} {'(RETRY)' if retry else ''}...")
        response = await client.post(WEBHOOK_URL, content=payload_str, headers=headers)
        print(f"Response: {response.status_code} - {response.text}")

async def main():
    event_id = "evt_test123"
    # Send the first request
    await send_mock_webhook(event_id)
    print("Waiting 2 seconds...")
    await asyncio.sleep(2)
    # Send the EXACT SAME request again to test idempotency
    await send_mock_webhook(event_id, retry=True)

if __name__ == "__main__":
    asyncio.run(main())
