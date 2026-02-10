# pytest tests/unit/test_sheets.py -v

import unittest
from schemas.product import Product

from services.integrations.printer_service import PrinterIntegration
printer = PrinterIntegration()

from services.integrations.sheets_service import SheetsService
sheets_service = SheetsService()

from tests.test_data.print_request import FULL_PRINT_REQUEST

from services.sales import SalesService
salesService = SalesService()

product_to_add = Product(
    row_number=3300,
    sku_no="3-281",
    im_sku="test",
    item_description="item description",
    selling_price=2000.00,
    quantity=1,
    date_bought="10.2.26",
    seller_name_address="seller name and address",
    purchase_price=1500.00,
    commission=0,
    date_sold=None,
    invoice_no_xero= None,
    on_website=False,
    location="location",
    sold=False,
    photograph=None
)

class TestSheets(unittest.TestCase):

    def test_add_product(self):
        sheets_service.add_product(product=product_to_add)
        pass

if __name__ == '__main__':
    unittest.main()