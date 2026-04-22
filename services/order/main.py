from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import engine, Base, get_db
from models import Order, OrderCreate, OrderResponse, OutboxEvent
from typing import List
import asyncio
from worker import outbox_worker, order_consumer_worker
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Order Service")

FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Start the background workers
    asyncio.create_task(outbox_worker())
    asyncio.create_task(order_consumer_worker())

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    # Create the order in PENDING state
    new_order = Order(
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        status="PENDING"
    )
    db.add(new_order)
    await db.flush() # flush to get the order ID

    # Create the Outbox Event within the SAME transaction
    event_payload = {
        "order_id": new_order.id,
        "user_id": new_order.user_id,
        "product_id": new_order.product_id,
        "quantity": new_order.quantity
    }
    
    outbox_event = OutboxEvent(
        aggregate_type="Order",
        aggregate_id=str(new_order.id),
        event_type="OrderCreated",
        payload=event_payload,
        status="PENDING"
    )
    db.add(outbox_event)
    
    # Commit both order and outbox event atomically
    await db.commit()
    await db.refresh(new_order)
    
    return new_order
