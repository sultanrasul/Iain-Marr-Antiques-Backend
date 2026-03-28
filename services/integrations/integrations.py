# integrations.py
from typing import Literal

from services.integrations.printer_service import PrinterIntegration
from services.integrations.sheets_service import SheetsService
from services.integrations.database_service import DatabaseService
from services.integrations.email_service import EmailService
from config import settings

printer_service = PrinterIntegration()
sheets_service = SheetsService()
database_service = DatabaseService(settings.DATABASE_PATH)
email_service = EmailService()

def get_printer_service():
    return printer_service

def get_sheets_service():
    return sheets_service

def get_database_service():
    return database_service

def get_email_service():
    return email_service

# helper to reset any integration
def reset_integration(name: Literal["printer", "sheets", "database", "email"]):
    global printer_service, sheets_service, database_service, email_service
    if name == "printer":
        printer_service = PrinterIntegration()
    elif name == "sheets":
        sheets_service = SheetsService()
    elif name == "database":
        database_service = DatabaseService()
    elif name == "email":
        email_service = EmailService()