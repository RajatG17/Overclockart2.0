import asyncio
import json
import uuid
from datetime import datetime, timezone

import aio_pika
from aio_pika import ExchangeType
from sqlalchemy import update

from .config import settings
from .database import SessionLocal
from .models import (
    Inventory,
    OutboxEvent,
    ProcessedEvent,
)


EXCHANGE_NAME = "commerce.events"
QUEUE_NAME = "catalog.inventory"

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
        durable=True
    )
    
    await queue.bind(
        exchange,
        routing_key = (
            "inventory.reserve.requested"
        )
    )
    
    await queue.bind(
        exchange,
        routing_key= (
            "inventory.release.requested"
        )
    )
    
    return connection, queue


async def reserve_items(
    db, 
    items: list[dict]
) -> bool:
    """_summary_

    Args:
        db (SessionLocal): database session
        items (list[dict]): order items

    Returns:
        bool: True if item quantity was reserved, False otherwise.
    """
    for item in items:
        product_id = uuid.UUID(
            item["product_id"]
        )
        
        quantity = int(
            item["quantity"]
        )
        
        statement = (
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.available_quantity >= quantity,
            )
            .values(
                available_quantity = (
                    Inventory.available_quantity - quantity
                ),
                reserved_quantity = (
                    Inventory.reserved_quantity + quantity
                ),
            )
        )
        
        result = await db.execute(
            statement
        )
        
        return result.rowcount != 0
    
async def handle_reservation_request(
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
            event_id,
        )
        
        if existing is not None:
            return 
        
        success = await reserve_items(
            db, 
            data["items"],
        )
        
        outgoing_event_id = uuid.uuid4()
        
        if success:
            event_type = "InventoryReserved"
        else:
            await db.rollback()
            
            event_type = (
                "InventoryReservationFailed"
            )
            
        outgoing_payload = {
            "event_id": str(
                outgoing_event_id
            ),
            "event_type": event_type,
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
                event_type=event_type,
                payload = outgoing_payload,
            )
        )
        
        db.add(
            ProcessedEvent(
                event_id=event_id,
                event_type=event["event_type"],
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
        
        if event_type == (
            "InventoryReservationRequested"
        ):
            await handle_reservation_request(
                event
            )
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
        
async def main() -> None:
    connection, queue = (await setup_rabbitmq())
    
    try:
        await queue.consume(process_message)
        
        print("Catalog inventory consumer started")
    
        await asyncio.Future()
    
    finally:
        await connection.close()
        
if __name__ == "__main__":
    asyncio.run(main())