from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from schemas.printRequest import PrintRequest
from services.sales import SalesService
salesService = SalesService()

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/print-request")
async def print_request(request: PrintRequest):
    """Print Request"""

    return salesService.checkout(request)
