# integrations.py
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