from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from services.system import SystemService
systemService = SystemService()

from services.integrations.integrations import get_printer_service
printerIntegration = get_printer_service()

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/restart")
async def restart_system():
    """Restarts the Raspberry Pi"""

    return systemService.restart_system()

@router.post("/shutdown")
async def shutdown_system():
    """Shuts down the Raspberry Pi"""

    return systemService.shutdown_system()

@router.get("/reconnect-printer")
async def reconnect_printer():
    """Reconnect the printer to the Raspberry Pi"""

    return printerIntegration.connect()