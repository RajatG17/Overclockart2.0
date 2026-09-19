import asyncio
import json
import uuid
from datetime import datetime, timezone

import aio_pika
from aio_pika import ExchangeType
from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .models import (
    Order,
    OrderStatus,
    OutboxEvent,
    ProcessedEvent,
)

EXCHANGE_NAME = "commerce.events"
QUEUE_NAME = "order.saga"

async def setup_rabbitmq():
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )
    
    channel = await connection.channel()
    
    await channel.set_qos(
        prefetch_count=10
    )
    
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True,
    )
    
    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
    )
    
    routing_keys = [
        "order.created",
        "inventory.reserved",
        "inventory.reservation_failed",
        "payment.succeeded",
        "payment.failed",
        "inventory.released",
    ]
    
    for routing_key in routing_keys:
        await queue.bind(
            exchange,
            routing_key=routing_key,
        )
    
    return connection, queue

async def handle_order_created(
    event: dict
) -> None:
    event_id = uuid.UUID(
        event["event_id"]
    )
    
    data = event["data"]
    
    order_id = uuid.UUID(
        data["order_id"]
    )
    
    async with SessionLocal() as db:
        existing = await db.get(
            ProcessedEvent,
            event_id,
        )
        
        if existing is not None:
            return
        
        order = await db.get(
            Order,
            order_id,
        )
        
        if order is None:
            raise RuntimeError(
                f"Order not found: {order_id}"
            )

        order.status = (
            OrderStatus.RESERVING_INVENTORY
        )
        
        outgoing_event_id = uuid.uuid4()
        
        outgoing_payload = {
            "event_id": str(
                outgoing_event_id
            ),
            "event_type": (
                "InventoryReservationRequested"
            ),
            "event_version": 1,
            "occured_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "data": {
                "order_id": str(order_id),
                "items": data["items"],
                "total": data["total"],
            },
        }
        
        db.add(
            OutboxEvent(
                id=outgoing_event_id,
                aggregate_id=order_id,
                event_type=(
                    "InventoryReservationRequested"
                ),
                payload=outgoing_payload,
            )
        )
        
        db.add(
            ProcessedEvent(
                event_id=event_id,
                event_type=event["event_type"],
            )
        )
        
        await db.commit()

async def handle_inventory_reserved(
    event: dict,
) -> None:
    event_id = uuid.UUID(
        event["event_id"]
    )
    
    data = event["data"]
    
    order_id = uuid.UUID(
        data["order_id"]
    )
    
    async with SessionLocal() as db:
        existing = await db.get(
            ProcessedEvent,
            event_id
        )
        
        if existing is not None:
            return 
        
        order = await db.get(
            Order,
            order_id
        )
        
        if order is None:
            raise RuntimeError(
                f"Order not found: {order_id}"
            )
            
        order.status = (
            OrderStatus.INVENTORY_RESERVED
        )
        
        outgoing_event_id = uuid.uuid4()
        
        outgoing_payload = {
            "event_id": str(
                outgoing_event_id
            ),
            "event_type": "PaymentRequested",
            "event_version": 1,
            "occured_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "data" :{
                "order_id": str(order_id),
                "total": data["total"],
                "items": data["items"],
            },
        }
        
        order.status = (
            OrderStatus.PAYMENT_PENDING
        )
        
        db.add(
            OutboxEvent(
                id=outgoing_event_id,
                aggregate_id = order_id,
                event_type="PaymentRequested",
                payload=outgoing_payload,
            )
        )
        
        db.add(
            ProcessedEvent(
                event_id = event_id,
                event_type = event["event_type"],
            )
        )
        
        await db.commit()
        
async def handle_inventory_failed(
    event: dict,
) -> None:
    event_id = uuid.UUID(
        event["event_id"]
    )
    
    order_id = uuid.UUID(
        event["data"]["order_id"]
    )
    
    async with SessionLocal() as db:
        existing = await db.get(
            ProcessedEvent,
            event_id
        )
        
        if existing is not None:
            return
        
        order = await db.get(
            Order,
            order_id,
        )
        
        if order is None:
            raise RuntimeError(
                f"Order not found: {order_id}"
            )
            
        order.status = OrderStatus.FAILED
        
        db.add(
            ProcessedEvent(
                event_id = event_id,
                event_type = event["event_type"],
            )
        )
        
        await db.commit()

async def process_message(
    message: aio_pika.IncomingMessage,
) -> None:
    try:
        event = json.loads(
            message.body.decode("utf-8")
        )
        
        
        event_type = event.get(
            "event_type"
        )
        
        if event_type == "OrderCreated":
            await handle_order_created(
                event
            )
        elif event_type == "InventoryReserved":
            await handle_inventory_reserved(event)
        elif event_type == "InventoryReservationFailed":
            await handle_inventory_failed(event)
        else:
            raise ValueError(
                f"Unsupported event type: {event_type}"
            )
        await message.ack()
        
    except Exception as exc:
        print(
            f"Failed processing message: {exc}"
        )
        
        await message.nack(
            requeue=True
        )

async def main()  -> None:
    connection, queue = (
        await setup_rabbitmq()
    )
    
    try:
        await queue.consume(
            process_message
        )
        
        print(
            "Order saga consumer started"
        )
        
        await asyncio.Future()
        
    finally:
        await connection.close()
        
if __name__ == "__main__":
    asyncio.run(main())