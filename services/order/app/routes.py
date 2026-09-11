from fastapi import APIRouter, Depends, HTTPException, status

import uuid
from decimal import Decimal
from fastapi import (
    APIRouter, 
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import get_db
from .models import (
    Order,
    OrderItem,
    OrderStatus,
    OutboxEvent,
)

from .schemas import (
    OrderCreateRequest,
    OrderResponse,
)

from datetime import datetime, timezone

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

def calculate_total(
        payload: OrderCreateRequest,
) -> Decimal:
    return sum(
        ( item.unit_price * item.quantity
        for item in payload.items 
        ),
        start=Decimal("0.00"),
    )

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> Order:
    order_id = uuid.uuid4()

    order = Order(
        id=order_id,
        user_id=payload.user_id,
        status=OrderStatus.PENDING,
        total=calculate_total(payload),
    )

    order_items = [
        OrderItem(
            order_id=order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in payload.items
    ]

    event_id = uuid.uuid4()

    event_payload = {
        "event_id": str(event_id),
        "event_type": "OrderCreated",
        "event_version": 1,
        "occured_at": datetime.now(
                    timezone.utc
                ).isoformat(),

        "data": {
            "order_id": str(order_id),
            "user_id": str(payload.user_id),
            "event_version": 1,
            "items": [
                {
                    "product_id": str(item.product_id),
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                }
                for item in payload.items
            ],
            "total": str(order.total), 
        },
    }

    outbox_event = OutboxEvent(
        id=event_id,
        aggregate_id=order_id,
        event_type="OrderCreated",
        payload=event_payload,
    )

    try:
        db.add(order)
        db.add_all(order_items)
        # await db.flush()

        # raise RuntimeError(
        #     "Rollback test"
        # )

        db.add(outbox_event)

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )

    return result.scalar_one()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id==order_id)
    )

    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order

@router.get(
    "",
    response_model=list[OrderResponse],
)
async def list_orders(
    db: AsyncSession = Depends(get_db)
) -> Order:

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    return list(
        result.scalars().all()
    )