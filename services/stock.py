from schemas.getSalesRequest import GetSalesRequest
from schemas.getStockRequest import GetStockRequest
from schemas.product import Product
from utils.exceptions import NotFoundError

from services.integrations.sheets_service import SheetsService
from utils.timing import timeit
sheets_service = SheetsService()

from services.integrations.printer_service import PrinterIntegration
printerService = PrinterIntegration()

from services.integrations.database_service import DatabaseService
databaseService = DatabaseService("database.sqlite")


class StockService:
    @staticmethod
    @timeit
    def get_stock(request: GetStockRequest):
        """
        Return all stock items from database
        """
        # return sheets_service.get_stock()
        return { "products": databaseService.get_stock(request), "printer_connected": printerService.connect() }
    
    @staticmethod
    def get_sales(request: GetSalesRequest):
        """
        Return all sales from database
        """
        # Extract query parameters from request body
        return databaseService.get_sales(request)

    @staticmethod
    def add_product(product: Product):
        """

        Add a new product to stock
        """

        sheets_new_product = sheets_service.add_product(product)
        databaseService.add_product(product)

        return sheets_new_product

    @staticmethod
    def modify_product(product: Product):
        """
        Modify an existing product by SKU
        """

        updated = sheets_service.update_product(product)

        if not updated:
            raise NotFoundError(f"Product with SKU {product.sku_no} not found")

        databaseService.modify_product(product)

        return updated
    
    @staticmethod
    def get_order_products(order_id: str):
        """
        Get products by order ID
        """

        return databaseService.get_order_products(order_id)