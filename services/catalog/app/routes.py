import uuid 

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Inventory, Product
from .schemas import (
    InventoryOperationRequest,
    InventoryResponse, 
    ProductCreateRequest, 
    ProductResponse,
)

router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
)

@router.post("/products",
             response_model=ProductResponse,
             status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    db: AsyncSession = Depends(get_db)
)-> Product:
    product= Product(
        name = payload.name,
        price = payload.price,
    )

    inventory = Inventory(
        product=product,
        available_quantity=payload.initial_quantity,
        reserved_quantity=0,
    )

    db.add(product)
    db.add(inventory)

    await db.commit()
    await db.refresh(product)

    return product

@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Product:
    product = await db.get(
        Product, 
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product

@router.get(
    "/products/{product_id}/inventory",
    response_model=InventoryResponse
)
async def get_inventory(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Inventory:
    inventory = await db.get(
        Inventory,
        product_id,
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found",
        )

    return inventory


@router.post(
    "/inventory/{product_id}/reserve",
    response_model=InventoryResponse,
)
async def reserve_inventory(
    product_id: uuid.UUID,
    payload: InventoryOperationRequest,
    db: AsyncSession = Depends(get_db)
) -> Inventory:
    statement = (
        update(Inventory)
        .where(
            Inventory.product_id == product_id,
            Inventory.available_quantity >= payload.quantity,
        )
        .values(
            available_quantity = (
                Inventory.available_quantity - payload.quantity
            ),
            reserved_quantity = (
                Inventory.reserved_quantity + payload.quantity
            ),
        )
    )

    result = await db.execute(statement)

    if result.rowcount == 0:
        await db.rollback()

        inventory = await db.get(
            Inventory, 
            product_id,
        )

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient inventory",
        )


    await db.commit()

    inventory = await db.get(
        Inventory, 
        product_id
    )

    return inventory  

@router.post(
    "/inventory/{product_id}/release",
    response_model=InventoryResponse,
)
async def release_inventory(
    product_id: uuid.UUID,
    payload: InventoryOperationRequest,
    db: AsyncSession = Depends(get_db),
) -> Inventory:
    statement = (
        update(Inventory)
        .where(
            Inventory.product_id == product_id,
            Inventory.reserved_quantity >= payload.quantity,
        )
        .values(
            available_quantity = (
                Inventory.available_quantity + payload.quantity
            ),
            reserved_quantity=(
                Inventory.reserved_quantity - payload.quantity
            ),
        )
    )

    result = await db.execute(statement)

    if result.rowcount == 0:
        await db.rollback()

        inventory = await db.get(
            Inventory,
            product_id,
        )

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not founc",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient reserved quantity"
        )

    await db.commit()

    inventory = await db.get(
        Inventory,
        product_id,
    )

    return inventory