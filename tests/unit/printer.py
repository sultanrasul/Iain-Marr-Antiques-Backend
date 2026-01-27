import unittest

from services.integrations.printer_service import PrinterIntegration
printer = PrinterIntegration()

from tests.test_data.print_request import FULL_PRINT_REQUEST

from services.sales import SalesService
salesService = SalesService()

class TestStringMethods(unittest.TestCase):

    def test_printer_connection(self):
        self.assertTrue(printer.connect())

    def test_receipt_printer(self):
        salesService.print_receipt(FULL_PRINT_REQUEST)
    
    def test_head_print(self):
        printer.print_header_image( printer_name="Star_TSP800_", image_path="/home/sultanrasul/backend/header.jpeg")
        printer.initialize()
        printer.feed(2)
        printer.cut()

if __name__ == '__main__':
    unittest.main()