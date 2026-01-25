import subprocess

from schemas.product import Product
from schemas.printRequest import PrintRequest
from utils.exceptions import PrinterNotConnected, http_exception_handler

from services.integrations.printer_service import PrinterIntegration
printer = PrinterIntegration()

from services.integrations.email_service import EmailService
emailService = EmailService()

from services.integrations.sheets_service import SheetsService
sheetsService = SheetsService()

class SalesService:
    @staticmethod
    def checkout(request: PrintRequest):
        # Check if printer is connected
        if request.copies !=0 and printer.connect() == False:
            raise http_exception_handler(exc=PrinterNotConnected())

        # Print the receipt(s)
        for _ in range (request.copies):
            SalesService.print_receipt(request)

        # Send Email
        if request.email_address:
            emailService.send_email(request)
            
        if request.mark_as_sold:
            pass
            # mark_as_sold

        
        return { "success": True, "sold_count": len(request.products) if request.mark_as_sold else 0, "printed_count": len(request.products)}

    @staticmethod
    def print_receipt(request: PrintRequest):

        printer.print_header_image( printer_name="Star_TSP800_", image_path="/home/sultanrasul/backend/header.jpeg")

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