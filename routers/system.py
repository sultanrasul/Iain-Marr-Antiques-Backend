from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from services.system import SystemService
systemService = SystemService()

from services.integrations.printer_service import PrinterIntegration
printerIntegration = PrinterIntegration()

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