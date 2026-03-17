from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from schemas.product import Product
from services.stock import StockService

router = APIRouter(prefix="/stock", tags=["stock"])

@router.get("/get-stock")
async def get_stock():
    """Get Stock"""

    return StockService.get_stock()

@router.post("/modify-product")
async def modify_product(request: Product):
    """Modify Product"""

    return StockService.modify_product(request)

@router.post("/add-product")
async def modify_product(request: Product):
    """Add Product"""

    return StockService.add_product(request)

@router.get("/{order_id}/products")
async def get_order_products(order_id: str):
    """Get all products in a specific order/sale"""
    return StockService.get_order_products(order_id)