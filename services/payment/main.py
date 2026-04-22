from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import stripe
import os
import json
import json
from redis_client import check_and_set_idempotency, redis_client
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Payment Service")

FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mocksecret")
stripe.api_key = os.getenv("STRIPE_API_KEY", "sk_test_mock")

@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    event = None
    try:
        # Cryptographic signature verification
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Enforce Idempotency
    event_id = event["id"]
    is_new_event = await check_and_set_idempotency(event_id)
    
    if not is_new_event:
        print(f"Idempotent request: Event {event_id} already processed.")
        # Return 200 immediately to Stripe
        return JSONResponse(content={"status": "already processed"}, status_code=200)

    # Process the event based on type
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print(f"Payment intent succeeded! Amount: {payment_intent.get('amount')}")
        # Here we would normally publish an event to RabbitMQ for Order Service to consume
    else:
        print(f"Unhandled event type: {event['type']}")

    # Return 2xx immediately to Stripe
    return JSONResponse(content={"status": "success"}, status_code=200)
