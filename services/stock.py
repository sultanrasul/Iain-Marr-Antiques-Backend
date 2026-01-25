from schemas.product import Product
from utils.exceptions import NotFoundError

from services.integrations.sheets_service import SheetsService
sheets_service = SheetsService()

from services.integrations.printer_service import PrinterIntegration
printerService = PrinterIntegration()


class StockService:
    @staticmethod
    def get_stock():
        """
        Return all stock items from Google Sheets
        """
        # return sheets_service.get_stock()
        return { "data": sheets_service.get_stock(), "printer_connected": printerService.connect() }

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
