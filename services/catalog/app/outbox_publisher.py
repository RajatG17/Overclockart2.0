import asyncio
import json
from datetime import datetime, timezone

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .events import routing_key_for
from .models import OutboxEvent

EXCHANGE_NAME = "commerce.events"
POLL_INTERVAL_SECONDS = 1
BATCH_SIZE = 50

async def connect_rabbitmq():
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )
    
    channel = await connection.channel(
        publisher_confirms=True
    )
    
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True,
    )
    
    return connection, exchange

async def publish_event(
    exchange: aio_pika.Exchange,
    event: OutboxEvent,
) -> None:
    routing_key = routing_key_for(event_type=event.event_type)
    
    body = json.dumps(
        event.payload
    ).encode("utf-8")
    
    message = Message(
        body=body,
        content_type="application/json",
        delivery_mode=DeliveryMode.PERSISTENT,
        message_id=str(event.id),
        type=event.event_type,
    )
    
    await exchange.publish(
        message,
        routing_key=routing_key,
    )

async def publish_batch(
    exchange: aio_pika.Exchange,
) -> int:
    async with SessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.published_at.is_(None)
            )
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
        )
        
        events = list(
            result.scalars().all()
        )
        
        published_count = 0
        
        for event in events:
            try:
                await publish_event(
                    exchange,
                    event,
                )
                
                event.published_at = datetime.now(
                    timezone.utc
                )
                
                await db.commit()
                
                published_count += 1
            
            except Exception as exc:
                await db.rollback()
                
                print(
                    f"Failed to publish event {event.id}: {exc}"
                ) 
                
        return published_count       

async def main() -> None:
    connection, exchange = (
        await connect_rabbitmq()
    )
    
    try:
        while True:
            await publish_batch(exchange)
            
            await asyncio.sleep(
                POLL_INTERVAL_SECONDS
            )
    finally:
        await connection.close()
        
if __name__ == "__main__":
    asyncio.run(main())