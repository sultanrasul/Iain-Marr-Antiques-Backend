import csv

from services.integrations.sheets_service import SheetsService
sheetsService = SheetsService()

sheetsService.add_order_ids()