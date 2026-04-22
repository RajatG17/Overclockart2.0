import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def check_and_set_idempotency(event_id: str) -> bool:
    """Returns True if event is NEW, False if already processed."""
    # SETNX: Set if not exists. Returns 1 if key was set, 0 if it already existed.
    # Expiration set to 24 hours (86400 seconds)
    is_new = await redis_client.set(f"stripe_event:{event_id}", "PROCESSED", ex=86400, nx=True)
    return bool(is_new)
