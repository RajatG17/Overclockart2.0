import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from services.order.app.routes import (
    create_order, 
    get_order, 
    list_orders,
    calculate_total
)
from services.order.app.schemas import OrderCreateRequest
from services.order.app.models import Order, OutboxEvent
from fastapi import HTTPException, status
import uuid
from decimal import Decimal

user_id = uuid.uuid4()

# Unit test for calculate_total helper
def test_calculate_total():
    items = [
        {"product_id": uuid.uuid4(), "quantity": 2, "unit_price": Decimal("10.00")},
        {"product_id": uuid.uuid4(), "quantity": 1, "unit_price": Decimal("5.00")}
    ]
    payload = OrderCreateRequest(user_id=user_id, items=items)
    # 2 * 10.50 + 1 * 5.00 = 21.00 + 5.00 = 26.00
    assert calculate_total(payload) == Decimal("25.00")

@pytest.mark.asyncio
async def test_create_order_success():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    payload = OrderCreateRequest(
        user_id=user_id, 
        items=[{
            "product_id": uuid.uuid4(), 
            "quantity": 2, 
            "unit_price": Decimal("10.00"),
        }]
    )

    # Mock the result of select(Order)...
    mock_result = MagicMock()
    mock_order = MagicMock(spec=Order)
    mock_order.id = uuid.uuid4()
    mock_order.total = Decimal("20.00")
    mock_result.scalar_one.return_value = mock_order
    mock_db.execute.return_value = mock_result

    # Act
    order = await create_order(payload, db=mock_db)

    # Assert
    assert order.total == Decimal("20.00")
    assert mock_db.add.called # For Order
    assert mock_db.add_all.called # For OrderItems
    assert mock_db.add.called # For OutboxEvent
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_get_order_not_found():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await get_order(uuid.uuid4(), db=mock_db)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_list_orders():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_orders = [MagicMock(spec=Order)]
    mock_result.scalars.return_value.all.return_value = mock_orders
    mock_db.execute.return_value = mock_result

    # Act
    orders = await list_orders(db=mock_db)

    # Assert
    assert len(orders) == 1
