from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from schemas.getStockRequest import GetStockRequest
from schemas.getSalesRequest import GetSalesRequest
from schemas.product import Product
from services.stock import StockService
from utils.timing import timeit

router = APIRouter(prefix="/stock", tags=["stock"])

@router.get("/get-stock")
@timeit
async def get_stock(request: GetStockRequest = Depends()):
    """Get Stock"""

    return StockService.get_stock(request)

@router.get("/get-sales")
async def get_sales(request: GetSalesRequest = Depends()):
    """Get Sales with filters"""
    # Extract query parameters from request body
    return StockService.get_sales(request)

@router.post("/modify-products")
async def modify_product(request: List[Product]):
    """Modify Product"""

    result = StockService.modify_products(request)

    if result is None:
        return {"message": "Products updated successfully"}

    if result == "Product not found":
        raise HTTPException(status_code=404, detail=result)

    if result == "SKU number already exists":
        raise HTTPException(status_code=409, detail=result)

    raise HTTPException(status_code=400, detail=result)

@router.post("/add-product")
async def add_product(request: Product):
    result = StockService.add_product(request)

    if result is None:
        return {"message": "Product added successfully"}

    if result == "SKU number already exists":
        raise HTTPException(status_code=409, detail=result)

    raise HTTPException(status_code=400, detail=result)

@router.get("/{order_id}/products")
async def get_order_products(order_id: str):
    """Get all products in a specific order/sale"""
    return StockService.get_order_products(order_id)