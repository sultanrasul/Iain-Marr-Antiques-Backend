from services.integrations.printer_service import PrinterIntegration
printer = PrinterIntegration()

from tests.test_data.print_request import FULL_PRINT_REQUEST

from services.sales import SalesService
salesService = SalesService()

from schemas.printRequest import PrintRequest
from schemas.product import Product


FULL_PRINT_REQUEST = PrintRequest(
    products=[
        Product(
            sku_no="IMA1",
            im_sku="529-308",
            item_description="Georgian silver waiter London 1778 10oz Troy",
            quantity=1,
            selling_price=0.0,  # blank in sheet
            date_bought="28.11.22",
            seller_name_address="Booker-Millburn",
            purchase_price=100.0,
            commission=0.0,
            date_sold="",
            invoice_no_xero="",
            on_website=False,
            location="",
            sold=False,
            photograph=""
        ),
        Product(
            sku_no="IMA2",
            im_sku="",
            item_description=(
                "2 items Silver coffee pot (27.5 ozs troy) and teapot "
                "(24oz troy). Maker Thomas Bradbury & Sons "
                "(Joseph & Edward Bradbury) London 1875."
            ),
            quantity=1,
            selling_price=1350.0,
            date_bought="",
            seller_name_address="",
            purchase_price=0.0,
            commission=0.0,
            date_sold="",
            invoice_no_xero="",
            on_website=False,
            location="",
            sold=False,
            photograph=""
        ),
        Product(
            sku_no="IMA3",
            im_sku="796-74",
            item_description=(
                "Scottish silver teapot Edinburgh 1876. "
                "Maker Mackays Chisholm 18oz Troy"
            ),
            quantity=1,
            selling_price=1400.0,
            date_bought="",
            seller_name_address="",
            purchase_price=0.0,
            commission=0.0,
            date_sold="",
            invoice_no_xero="",
            on_website=False,
            location="",
            sold=False,
            photograph=""
        ),
    ],
    mark_as_sold=False,
    copies=1,
    customer_name="Sultan Rasul",
    email_address="",
)

salesService.print_receipt(FULL_PRINT_REQUEST)