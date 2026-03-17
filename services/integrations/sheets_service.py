import json
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from config import settings
from gspread_formatting import *

from schemas.printRequest import PrintRequest
from schemas.product import Product
from schemas.soldProduct import SoldProduct
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
        print(f"Starting Connection to google sheets with the ID: {sheet_id}")
        self.workbook = self.client.open_by_key(sheet_id)

        # Worksheets
        self.items = self.workbook.sheet1
        self.sold_items = self.workbook.get_worksheet(1)

        # Optional: useful shared values
        self.today = datetime.now()

        self.fmt_red = CellFormat(backgroundColor=Color(0.9019607843137255, 0.0, 0.054901960784313725))

    def get_stock(self) -> List[Product]:
        """Fetch all rows from the sheet and convert them into Product instances."""
        rows = self.items.get_all_records()
        products = [
         Product.from_sheet_row({**row, "row_number": i + 2})  # +2 if row 1 is headers
         for i, row in enumerate(rows)
        ]
        return products

    
    def find_row_index_by_sku(self, sku: str) -> Optional[tuple[int, Product]]:
        records = self.items.get_all_records()
        for i, rec in enumerate(records, start=2):  # row 1 is header
            if str(rec.get("SKU NO.", "")).strip() == sku.strip():
                product = Product.from_sheet_row(
                    {**rec, "row_number": i}
                )
                return i, product
        return None
    
    @timeit
    def update_product(self, product: Product) -> bool:
        current_row_values = self.items.row_values(product.row_number)
        
        if current_row_values[0] != product.sku_no:
            # Row shifted! Fall back to search by SKU
            row_index, _ = self.find_row_index_by_sku(product.sku_no)
            if row_index is None:
                return False 
            product.row_number = row_index  # update cached row_number
        
        headers = self.items.row_values(1)
        row_data = product.to_sheet_row()
        self.items.update( f"A{product.row_number}:{chr(64 + len(headers))}{product.row_number}", [row_data] )
        return True

    
    def add_product(self, product: Product):
        self.items.append_row(product.to_sheet_row(), value_input_option="USER_ENTERED")

    def mark_row_sold_red(self, row_number: int):
        headers = self.items.row_values(1)
        format_cell_range( self.items, f"B{row_number}:{chr(64 + len(headers))}{row_number}", self.fmt_red )

    def get_sold_items(self) -> List[SoldProduct]:
        rows = self.sold_items.get_all_records(
            value_render_option="UNFORMATTED_VALUE"
        )

        for row in rows:
            raw_value = row.get("DATE SOLD")

            if isinstance(raw_value, (int, float)):
                # Convert Google Sheets serial → real datetime
                real_date = datetime(1899, 12, 30) + timedelta(days=raw_value)

                row["DATE SOLD"] = real_date.strftime("%Y-%m-%d %H:%M:%S")  # SQLite format

        return [
            SoldProduct.from_sheet_row({**row, "row_number": i + 2})
            for i, row in enumerate(rows)
        ]
    
    def add_sold_product(self, product: SoldProduct):
        self.sold_items.append_row(product.to_sheet_row(), value_input_option="USER_ENTERED")
    
    def update_sold_product(self, product: SoldProduct) -> bool:
        headers = self.sold_items.row_values(1)
        self.sold_items.update(
            f"A{product.row_number}:{chr(64 + len(headers))}{product.row_number}",
            [product.to_sheet_row()]
        )
        return True
    
    def mark_as_sold(self, request: PrintRequest):
        all_records = self.items.get_all_records()
        # date_sold = datetime.now().strftime("%-d.%-m.%y %H:%M")
        date_sold = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # SQLite format

        for product in request.products:

            row_index = None
            record_row = None

            # Find row in Items
            for i, record in enumerate(all_records, start=2):  # start=2 because header is row 1
                if str(record.get("SKU NO.")).strip() == product.sku_no:
                    row_index = i
                    record_row = record
                    break
            
            if not row_index or not record_row:
                continue  # skip if SKU not found

            quantity_sold = product.quantity               # the number being sold

            # If the Quantity Row is empty set it to 1
            sheet_quantity = int(record_row.get("Quantity") or 1)
            remaining_quantity = max(0, sheet_quantity - quantity_sold)

            product.quantity = remaining_quantity
            product.sold = True if remaining_quantity == 0 else False

            self.update_product(product)

            # Done through "Conditional Formatting" in Google Sheets
            # if product.sold:
            #     self.mark_row_sold_red(row_index)

            soldProduct: SoldProduct = SoldProduct.from_product(product=product, customer_name=request.customer_name,quantity=quantity_sold,date_sold=date_sold,total_price=quantity_sold*product.selling_price)
            self.add_sold_product(soldProduct)
        
        return True
    
    def convert_old_date_format(self):
        sold_products = self.get_sold_items()
        headers = self.sold_items.row_values(1)

        updated_rows = []
        row_ranges = []

        for product in sold_products:
            old_date = product.date_sold

            if not old_date or "/" in old_date:
                continue  # skip already converted

            try:
                parsed_date = datetime.strptime(old_date.strip(), "%d.%m.%y %H:%M")
                new_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")  # SQLite format

                product.date_sold = new_date

                row_data = product.to_sheet_row()
                row_range = f"A{product.row_number}:{chr(64 + len(headers))}{product.row_number}"

                row_ranges.append(row_range)
                updated_rows.append(row_data)

            except ValueError:
                continue

        # 🚀 Batch update instead of per-row update
        if row_ranges:
            data = [
                {"range": r, "values": [v]}
                for r, v in zip(row_ranges, updated_rows)
            ]
            self.sold_items.batch_update(data)