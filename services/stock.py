from schemas.getSalesRequest import GetSalesRequest
from schemas.getStockRequest import GetStockRequest
from schemas.product import Product
from services.system import SystemService
from utils.exceptions import NotFoundError

from utils.timing import timeit

from services.integrations.integrations import get_sheets_service, get_database_service, get_printer_service


class StockService:
    @staticmethod
    @timeit
    def get_stock(request: GetStockRequest):
        """
        Return all stock items from database
        """
        databaseService = get_database_service()
        printerService = get_printer_service()
        systemService = SystemService()
        # return sheets_service.get_stock()
        return { "products": databaseService.get_stock(request), "printer_connected": printerService.connect(), "stats": databaseService.get_table_stats(), "settings": systemService.get_settings() }
    
    @staticmethod
    def get_sales(request: GetSalesRequest):
        """
        Return all sales from database
        """
        databaseService = get_database_service()
        # Extract query parameters from request body
        return databaseService.get_sales(request)

    @staticmethod
    def add_product(product: Product):
        """

        Add a new product to stock
        """
        sheetsService = get_sheets_service()
        databaseService = get_database_service()
        sheets_new_product = sheetsService.add_product(product)
        databaseService.add_product(product)

        return sheets_new_product

    @staticmethod
    def modify_product(product: Product):
        """
        Modify an existing product by SKU
        """
        sheetsService = get_sheets_service()
        databaseService = get_database_service()
        updated = sheetsService.update_product(product)

        if not updated:
            raise NotFoundError(f"Product with SKU {product.sku_no} not found")

        databaseService.modify_product(product)

        return updated
    
    @staticmethod
    def get_order_products(order_id: str):
        """
        Get products by order ID
        """
        databaseService = get_database_service()
        return databaseService.get_order_products(order_id)