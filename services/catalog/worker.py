import asyncio
import os
import json
import aio_pika
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models import Product

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def process_order_created(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body.decode())
        order_id = event["order_id"]
        product_id = event["product_id"]
        quantity = event["quantity"]

        async with AsyncSessionLocal() as session:
            # Check and reserve stock
            result = await session.execute(select(Product).where(Product.id == product_id))
            product = result.scalars().first()
            
            success = False
            if product and product.stock >= quantity:
                product.stock -= quantity
                session.add(product)
                await session.commit()
                success = True
            else:
                await session.rollback()
            
            # Emit outcome event
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("saga_exchange", aio_pika.ExchangeType.TOPIC)
                
                outcome_event_type = "StockReserved" if success else "StockReservationFailed"
                outcome_payload = {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity
                }
                
                out_message = aio_pika.Message(
                    body=json.dumps(outcome_payload).encode(),
                    content_type="application/json",
                    type=outcome_event_type
                )
                
                routing_key = f"catalog.{outcome_event_type.lower()}"
                await exchange.publish(out_message, routing_key=routing_key)
                print(f"Catalog processed Order {order_id}: {outcome_event_type}")

async def catalog_worker():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            exchange = await channel.declare_exchange("saga_exchange", aio_pika.ExchangeType.TOPIC)
            
            # Queue for Catalog Service to receive Order events
            queue = await channel.declare_queue("catalog_order_events", durable=True)
            await queue.bind(exchange, routing_key="order.ordercreated")
            
            print("Catalog worker waiting for messages...")
            await queue.consume(process_order_created)
            
            # Keep worker alive
            await asyncio.Future() 
        except Exception as e:
            print(f"Catalog worker error: {e}")
            await asyncio.sleep(5)
