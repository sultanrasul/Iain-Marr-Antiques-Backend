import json
from typing import List, Optional
import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from config import settings
from gspread_formatting import *

from schemas.printRequest import PrintRequest
from schemas.product import Product
from schemas.soldProduct import SoldProduct
from utils.timing import timeit
import copy

class SheetsService:
    @timeit
    def __init__(self):
        # Load credentials from env
        service_account_info = settings.GOOGLE_SERVICE_ACCOUNT_JSON

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        self.creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )

        self.client = gspread.authorize(self.creds)

        sheet_id = settings.GOOGLE_SHEETS_ID
        print(f"Starting Connection to google sheets with the ID: {sheet_id}")
        self.workbook = self.client.open_by_key(sheet_id)

        # Worksheets
        self.items = self.workbook.sheet1
        self.sold_items = self.workbook.get_worksheet(1)

        # Optional: useful shared values
        self.today = datetime.now()

        self.fmt_red = CellFormat(backgroundColor=Color(0.9019607843137255, 0.0, 0.054901960784313725))

    @timeit
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

    @timeit
    def get_sold_items(self) -> List[SoldProduct]:
        # 1. Get formatted values (default)
        formatted_rows = self.sold_items.get_all_records()

        # 2. Get unformatted values
        raw_rows = self.sold_items.get_all_records(
            value_render_option="UNFORMATTED_VALUE"
        )

        # 3. Merge DATE SOLD only
        for f_row, r_row in zip(formatted_rows, raw_rows):
            raw_date = r_row.get("DATE SOLD")

            if isinstance(raw_date, (int, float)):
                real_date = datetime(1899, 12, 30) + timedelta(days=raw_date)
                f_row["DATE SOLD"] = real_date.strftime("%Y-%m-%d %H:%M:%S")

        return [
            SoldProduct.from_sheet_row({**row, "row_number": i + 2})
            for i, row in enumerate(formatted_rows)
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

        # ✅ STEP 1: Get last order info from sold sheet
        sold_rows = self.sold_items.get_all_records()

        next_order_id = 1

        if sold_rows:
            last_row = sold_rows[-1]

            last_order_id = last_row.get("ORDER ID")
            last_date_sold = last_row.get("DATE SOLD")

            try:
                last_order_id = int(last_order_id) if last_order_id else None
            except ValueError:
                last_order_id = None

            if last_order_id:
                if last_date_sold == request.date_sold:
                    next_order_id = last_order_id  # same order
                else:
                    next_order_id = last_order_id + 1

        # ✅ STEP 2: Process products
        for product in request.products:

            row_index = None
            record_row = None

            # Find row in Items
            for i, record in enumerate(all_records, start=2):
                if str(record.get("SKU NO.")).strip() == product.sku_no:
                    row_index = i
                    record_row = record
                    break

            if not row_index or not record_row:
                continue

            quantity_sold = product.quantity
            sheet_quantity = int(record_row.get("Quantity") or 1)
            remaining_quantity = max(0, sheet_quantity - quantity_sold)

            product.quantity = remaining_quantity
            product.sold = True if remaining_quantity == 0 else False

            self.update_product(product)

            # ✅ CREATE SOLD PRODUCT WITH ORDER ID
            soldProduct: SoldProduct = SoldProduct.from_product(
                product=product,
                customer_name=request.customer_name,
                quantity=quantity_sold,
                date_sold=request.date_sold,
                total_price=quantity_sold * product.selling_price,
            )

            # 🔥 Assign order_id here
            soldProduct.order_id = next_order_id

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
    
    @timeit
    def get_last_modified(self) -> datetime:
        """Return the last modified time of the Google Sheet."""
        # Use the same credentials you created for gspread
        drive_service = build('drive', 'v3', credentials=self.creds)
        
        # Get the file metadata
        file = drive_service.files().get(
            fileId=self.workbook.id,
            fields="modifiedTime"
        ).execute()
        
        # Parse ISO timestamp to datetime
        last_modified = datetime.fromisoformat(file['modifiedTime'].replace("Z", "+00:00"))
        return last_modified
    
    def add_order_ids(self):
        sheet = self.sold_items

        # 1. Get headers
        headers = sheet.row_values(1)

        order_id_col_name = "ORDER ID"

        # 2. Ensure column exists in correct position
        if order_id_col_name not in headers:
            try:
                im_sku_index = headers.index("IM SKU")
            except ValueError:
                raise Exception("IM SKU column not found")

            insert_position = im_sku_index + 2  # +1 for next col, +1 because gspread is 1-based

            sheet.add_cols(1)

            # Shift columns right by inserting at position
            sheet.insert_cols(
                [[]],  # empty column
                col=insert_position
            )

            sheet.update_cell(1, insert_position, order_id_col_name)

            # Refresh headers
            headers = sheet.row_values(1)

        order_id_index = headers.index(order_id_col_name)
        date_sold_index = headers.index("DATE SOLD")

        # 3. Get all rows
        rows = sheet.get_all_values(value_render_option="UNFORMATTED_VALUE")[1:]

        updates = []

        current_order_id = 1
        previous_time = None

        for i, row in enumerate(rows, start=2):  # start=2 because header is row 1
            # Ensure row is long enough
            if len(row) <= date_sold_index:
                continue
    
            raw_value = row[date_sold_index]

            if not raw_value:
                continue

            current_time = SoldProduct.gs_to_datetime(raw_value)

            if not current_time:
                continue

            # Compare with previous row time
            if previous_time is None:
                # first valid row
                pass
            elif current_time != previous_time:
                current_order_id += 1

            previous_time = current_time

            # Set ORDER ID value
            cell_ref = gspread.utils.rowcol_to_a1(i, order_id_index + 1)
            updates.append({
                "range": cell_ref,
                "values": [[current_order_id]]
            })

        # 4. Batch update
        if updates:
            sheet.batch_update(updates)

        