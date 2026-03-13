import textwrap
import subprocess
import time
from datetime import datetime
from typing import Union
import usb.core
import usb.util


class PrinterIntegration:
    def __init__(self, vendor_id: int = 0x0519, product_id: int = 0x0001):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.dev = None
        self.printer = None
        self.line_width = 68


    def ensure_connected(self):
        if not self.is_connected():
            self.connect()

    def connect(self) -> bool:
        """
        Attempt to connect to the printer.
        Returns True if connected, False otherwise.
        """
        try:
            self.dev = usb.core.find(idVendor=self.vendor_id,idProduct=self.product_id)

            if self.dev is None:
                self.printer = None
                return False

            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)

            self.dev.set_configuration()
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]

            self.printer = usb.util.find_descriptor( 
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )

            return self.printer is not None

        except Exception:
            self.dev = None
            self.printer = None

            return False

    def is_connected(self) -> bool:
        return self.printer is not None
    

    def write(self, data: bytes):
        if not self.printer:
            raise RuntimeError("Printer not connected")
        self.printer.write(data)

    def dispose(self):
        if self.dev:
            usb.util.dispose_resources(self.dev)
            self.dev = None
            self.printer = None

    # --------------------------------------------------
    # HEADER (CUPS IMAGE – REAL PRINT)
    # --------------------------------------------------
    def print_header_image( self, printer_name: str, image_path: str ):
        result = subprocess.run(
            [
                "lp",
                "-d", printer_name,
                "-o", "scaling=100",
                "-o", "fit-to-page",
                "-o", "orientation-requested=3",
                image_path
            ],
            capture_output=True,
            text=True
        )

        job_output = result.stdout.strip()
        if not job_output:
            raise RuntimeError("Failed to submit logo print job")

        job_id = job_output.split(" ")[3]

        while True:
            stat = subprocess.run(
                ["lpstat", "-W", "not-completed"],
                capture_output=True,
                text=True
            ).stdout

            if job_id not in stat:
                break

            time.sleep(0.5)

    # --------------------------------------------------
    # BASIC ESC/POS COMMANDS (REAL)
    # --------------------------------------------------
    def initialize(self):
        self.write(b'\x1b\x40')

    def set_uk_charset(self):
        # Select UK character set (for £ symbol)
        self.write(b'\x1b\x74\x01')

    def bold_on(self):
        self.write(b'\x1b\x45')

    def bold_off(self):
        self.write(b'\x1b\x46')

    def feed(self, lines: int = 1):
        self.write(b'\n' * lines)

    def cut(self):
        self.write(b'\x1b\x64\x02')

    def align_left(self):
        # ESC GS a 0 → Left align
        self.write(b'\x1b\x1d\x61\x00')

    def align_center(self):
        # ESC GS a 1 → Center align
        self.write(b'\x1b\x1d\x61\x01')

    def align_right(self):
        # ESC GS a 2 → Right align
        self.write(b'\x1b\x1d\x61\x02')

    # --------------------------------------------------
    # HEADER LINE
    # --------------------------------------------------
    def header_date_line(self, customer_name: str = ""):
        today = datetime.now().strftime("%-d.%-m.%y")

        self.bold_on()

        if customer_name:
            self.print_total_line( f"Sold To: {customer_name}", f"Date: {today}", currency=False )
        else:
            self.print_total_line( "", f"Date: {today}", currency=False)

        self.bold_off()
        self.feed()

    # --------------------------------------------------
    # PRINT HELPERS
    # --------------------------------------------------
    def print_total_line( self, label: str, value: str, currency: bool = True ):
        
        spaces = self.line_width - len(label) - len(value) - (2 if currency else 1)
        spaces = max(spaces, 1)

        total_len = len(label) + spaces + (2 if currency else 1) + len(value)


        self.write(label.encode("cp1252"))
        self.write(b" " * spaces)

        if currency:
            self.write(b"\xA3")

        self.write(value.encode("cp1252"))

    def print_item( self, item_id: Union[int, str] , name: str, price: str, longest_id: int):
        padding = " " * (longest_id - len(str(item_id)))
        prefix = f"{item_id}{padding} - "
        left = f"{prefix}{name}"

        available_width = self.line_width - len(price) - 6

        wrapped = textwrap.wrap( left, available_width, subsequent_indent=" " * len(prefix) )

        for i, line in enumerate(wrapped):
            if i == 0:
                spaces = self.line_width - len(line) - len(price) - 2
                spaces = max(spaces, 1)

                self.write(line.encode("cp1252"))
                self.write(b" " * spaces)
                self.write(b"\xA3")
                self.write(price.encode("cp1252"))
            else:
                self.write(line.encode("cp1252"))

            self.feed()

        self.feed()

    # --------------------------------------------------
    # TOTALS
    # --------------------------------------------------
    def print_subtotal(self, value: float):
        self.print_total_line("Subtotal:", f"{value:.2f}")

    def print_total(self, value: float):
        self.bold_on()
        self.print_total_line("TOTAL:", f"{value:.2f}")
        self.bold_off()

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------
    def print_vat_footer(self):
        self.write(b"VAT Reg No. 2965 743 08\n")
        self.write(b"VAT has not been charged on the above items.\n")
