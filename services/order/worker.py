import asyncio
import os
import json
import aio_pika
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models import OutboxEvent

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def publish_message(connection: aio_pika.RobustConnection, event: OutboxEvent):
    channel = await connection.channel()
    exchange = await channel.declare_exchange("saga_exchange", aio_pika.ExchangeType.TOPIC)
    
    message_body = json.dumps(event.payload).encode()
    message = aio_pika.Message(
        body=message_body,
        content_type="application/json",
        message_id=str(event.id),
        type=event.event_type
    )
    
    routing_key = f"{event.aggregate_type.lower()}.{event.event_type.lower()}"
    await exchange.publish(message, routing_key=routing_key)

async def outbox_worker():
    while True:
        try:
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            
            async with connection:
                while True:
                    async with AsyncSessionLocal() as session:
                        # Poll for pending outbox events
                        result = await session.execute(
                            select(OutboxEvent).where(OutboxEvent.status == "PENDING").limit(10)
                        )
                        events = result.scalars().all()
                        
                        for event in events:
                            try:
                                # Publish to broker
                                await publish_message(connection, event)
                                
                                # Mark as processed
                                event.status = "PROCESSED"
                                session.add(event)
                                await session.commit()
                                print(f"Published event {event.id} ({event.event_type})")
                            except Exception as e:
                                print(f"Failed to publish event {event.id}: {e}")
                                await session.rollback()
                                
                    # Wait before next poll iteration
                    await asyncio.sleep(2)
                    
        except Exception as e:
            print(f"Worker connection error: {e}")
            await asyncio.sleep(5)
