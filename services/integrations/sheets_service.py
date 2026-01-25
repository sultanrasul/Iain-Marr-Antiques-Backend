import json
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import settings

from schemas.product import Product
from utils.timing import timeit

class SheetsService:
    def __init__(self):
        # Load credentials from env
        service_account_info = settings.GOOGLE_SERVICE_ACCOUNT_JSON

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )

        self.client = gspread.authorize(creds)

        sheet_id = settings.GOOGLE_SHEETS_ID
        self.workbook = self.client.open_by_key(sheet_id)

        # Worksheets
        self.items = self.workbook.sheet1
        self.sold_items = self.workbook.get_worksheet(1)

        # Optional: useful shared values
        self.today = datetime.now()




    def get_stock(self) -> List[Product]:
        """Fetch all rows from the sheet and convert them into Product instances."""
        rows = self.items.get_all_records()
        products = [
         Product.from_sheet_row({**row, "row_number": i + 2})  # +2 if row 1 is headers
         for i, row in enumerate(rows)
        ]
        print(products[0])
        return products

    
    def find_row_index_by_sku(self, sku: str) -> Optional[int]:
        records = self.items.get_all_records()
        for i, rec in enumerate(records, start=2):  # row 1 is header
            if str(rec.get("SKU NO.", "")).strip() == sku.strip():
                return i
        return None
    
    @timeit
    def update_product(self, product: Product) -> bool:
        current_row_values = self.items.row_values(product.row_number)
        
        if current_row_values[0] != product.sku_no:
            # Row shifted! Fall back to search by SKU
            row_index = self.find_row_index_by_sku(product.sku_no)
            if row_index is None:
                return False
            product.row_number = row_index  # update cached row_number
        
        headers = self.items.row_values(1)
        row_data = product.to_sheet_row()
        self.items.update(
            f"A{product.row_number}:{chr(64 + len(headers))}{product.row_number}",
            [row_data]
        )
        return True

    
    def add_product(self, product: Product):
        self.items.append_row(product.to_sheet_row(), value_input_option="USER_ENTERED")