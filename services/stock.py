from schemas.product import Product
from utils.exceptions import NotFoundError

from services.integrations.sheets_service import SheetsService
sheets_service = SheetsService()

from services.integrations.printer_service import PrinterIntegration
printerService = PrinterIntegration()

from services.integrations.database_service import DatabaseService
databaseService = DatabaseService("database.sqlite")


class StockService:
    @staticmethod
    def get_stock():
        """
        Return all stock items from Google Sheets
        """
        # return sheets_service.get_stock()
        return { "products": databaseService.get_stock(),"sales": databaseService.get_sales(), "printer_connected": printerService.connect() }

    @staticmethod
    def add_product(product: Product):
        """

        Add a new product to stock
        """
        return sheets_service.add_product(product)

    @staticmethod
    def modify_product(product: Product):
        """
        Modify an existing product by SKU
        """

        updated = sheets_service.update_product(product)

        if not updated:
            raise NotFoundError(f"Product with SKU {product.sku_no} not found")

        return updated
    
    @staticmethod
    def get_order_products(order_id: str):
        """
        Get products by order ID
        """

        return databaseService.get_order_products(order_id)