import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from services.catalog.app.routes import (
    create_product, 
    get_product, 
    get_inventory, 
    reserve_inventory, 
    release_inventory
)
from services.catalog.app.schemas import ProductCreateRequest, InventoryOperationRequest
from services.catalog.app.models import Product, Inventory
from fastapi import HTTPException, status
from decimal import Decimal
import uuid

@pytest.mark.asyncio
async def test_create_product_success():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    payload = ProductCreateRequest(name="Test Product", price=Decimal("99.99"), initial_quantity=10)

    # Act
    product = await create_product(payload, db=mock_db)

    # Assert
    assert product.name == "Test Product"
    assert product.price == Decimal("99.99")
    assert mock_db.add.call_count >= 2 # product and inventory
    assert mock_db.commit.called
    assert mock_db.refresh.called

@pytest.mark.asyncio
async def test_get_product_not_found():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.get.return_value = None
    product_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await get_product(product_id, db=mock_db)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Product not found" in excinfo.value.detail

@pytest.mark.asyncio
async def test_reserve_inventory_success():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    product_id = uuid.uuid4()
    payload = InventoryOperationRequest(quantity=5)
    
    # Mock update result
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result
    
    # Mock the subsequent get call after commit
    mock_inventory = MagicMock(spec=Inventory)
    mock_inventory.id = product_id
    mock_db.get.return_value = mock_inventory

    # Act
    result = await reserve_inventory(product_id, payload, db=mock_db)

    # Assert
    assert result == mock_inventory
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_reserve_inventory_insufficient():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    product_id = uuid.uuid4()
    payload = InventoryOperationRequest(quantity=100)
    
    # Mock update result with 0 rows affected (condition not met)
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute.return_value = mock_result
    
    # Mock the subsequent get call for error reporting
    mock_inventory = MagicMock(spec=Inventory)
    mock_inventory.id = product_id
    mock_db.get.return_value = mock_inventory

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await reserve_inventory(product_id, payload, db=mock_db)
    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient inventory" in excinfo.value.detail

@pytest.mark.asyncio
async def test_release_inventory_success():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    product_id = uuid.uuid4()
    payload = InventoryOperationRequest(quantity=5)
    
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result
    
    mock_inventory = MagicMock(spec=Inventory)
    mock_inventory.id = product_id
    mock_db.get.return_value = mock_inventory

    # Act
    result = await release_inventory(product_id, payload, db=mock_db)

    # Assert
    assert result == mock_inventory
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_release_inventory_insufficient():
    # Arrange
    mock_db = AsyncMock(spec=AsyncSession)
    product_id = uuid.uuid4()
    payload = InventoryOperationRequest(quantity=100)
    
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute.return_value = mock_result
    
    mock_inventory = MagicMock(spec=Inventory)
    mock_inventory.id = product_id
    mock_db.get.return_value = mock_inventory

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await release_inventory(product_id, payload, db=mock_db)
    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient reserved quantity" in excinfo.value.detail
