from fastapi import APIRouter, Body, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.system import SystemService
from fastapi.responses import FileResponse

from config import settings
import os

systemService = SystemService()

from services.integrations.integrations import get_printer_service
printerIntegration = get_printer_service()

router = APIRouter(prefix="/system", tags=["system"])

# ---------------- Existing endpoints ---------------- #
@router.get("/sync")
async def sync_database():
    """Imports Google Sheets Records into the database"""
    return systemService.sync_database()

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

# ---------------- New endpoints ---------------- #

@router.post("/update-sheets-id")
async def update_google_sheets_id(new_id: str = Body(..., embed=True)):
    """Update the Google Sheets ID dynamically"""
    return systemService.update_google_sheets_id(new_id)

@router.post("/upload-database")
async def upload_database(
    file: UploadFile = File(...),
    new_name: str = Form(None)
):
    """
    Upload a new database file.
    - file: the uploaded database
    - new_name: optional new filename, defaults to uploaded filename
    """
    db_name = new_name if new_name else file.filename
    content = await file.read()
    return systemService.upload_database_file(content, db_name)


@router.get("/download-database")
async def download_database():
    """Download the current database file"""
    db_path = settings.DATABASE_PATH
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found")
    # Serve in binary-safe way
    return FileResponse(path=db_path, filename=os.path.basename(db_path), media_type="application/octet-stream")