import subprocess

from schemas.product import Product
from schemas.printRequest import PrintRequest
from schemas.soldProduct import SoldProduct
from utils.exceptions import PrinterNotConnected, http_exception_handler


from services.integrations.integrations import get_sheets_service, get_database_service, get_email_service, get_printer_service
# databaseService = get_database_service()
# sheetsService = get_sheets_service()
# emailService = get_email_service()
# printer = get_printer_service()

class SalesService:
    @staticmethod
    def checkout(request: PrintRequest):
        databaseService = get_database_service()
        sheetsService = get_sheets_service()
        emailService = get_email_service()
        printer = get_printer_service()


        order_id: str = None

        # Check if printer is connected
        if request.copies !=0 and printer.connect() == False:
            raise http_exception_handler(exc=PrinterNotConnected())

        if request.mark_as_sold:
            # Add sale to Google Sheets
            # sheetsService.mark_as_sold(request)

            # Add sale to Database
            order_id = databaseService.add_sold_product(request)

        # Print the receipt(s)
        for _ in range (request.copies):
            SalesService.print_receipt(request)

        # Send Email
        if request.email_address:
            emailService.send_email(request)
        
        return { "success": True, "sold_count": len(request.products) if request.mark_as_sold else 0, "printed_count": len(request.products)}

    @staticmethod
    def print_receipt(request: PrintRequest, order_id: str):
        printer = get_printer_service() 
        printer.ensure_connected()

        printer.print_header_image( printer_name="Star_TSP800_", image_path="/home/sultanrasul/backend-fastapi/header.jpeg")

        printer.initialize()
        printer.set_uk_charset()
        printer.align_left()

        printer.feed(2)

        printer.header_date_line(request.customer_name)
        
        printer.feed(2)

        longest_id = max(len(str(product.sku_no)) for product in request.products)
        for product in request.products:
            printer.print_item( product.sku_no, product.item_description, f"{product.selling_price:.2f}", longest_id )

        total = SalesService.calculate_total(request)

        printer.print_subtotal(total)
        printer.feed()
        printer.print_total(total)

        printer.feed(2)

        printer.print_vat_footer()

        printer.feed(2)

        printer.cut()

        printer.dispose()
    
    @staticmethod
    def calculate_total(request: PrintRequest):
        total_price = 0.00
        for product in request.products:
            total_price = total_price + float(product.selling_price * float(product.quantity))
        return total_price
