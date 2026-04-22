import asyncio
import os
import json
import aio_pika
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models import OutboxEvent, Order

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

async def process_saga_outcome(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body.decode())
        order_id = int(event["order_id"])
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalars().first()
            if order:
                if message.type == "StockReserved":
                    order.status = "CONFIRMED"
                elif message.type == "StockReservationFailed":
                    order.status = "CANCELLED"
                session.add(order)
                await session.commit()
                print(f"Order {order_id} transitioned to {order.status}")

async def order_consumer_worker():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            exchange = await channel.declare_exchange("saga_exchange", aio_pika.ExchangeType.TOPIC)
            
            queue = await channel.declare_queue("order_saga_outcomes", durable=True)
            await queue.bind(exchange, routing_key="catalog.stockreserved")
            await queue.bind(exchange, routing_key="catalog.stockreservationfailed")
            
            print("Order consumer waiting for Saga outcomes...")
            await queue.consume(process_saga_outcome)
            
            await asyncio.Future() 
        except Exception as e:
            print(f"Order consumer error: {e}")
            await asyncio.sleep(5)
