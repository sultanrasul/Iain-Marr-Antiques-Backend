import usb.core, usb.util
import textwrap
import subprocess
import time

# --------------------------------------------------
# STEP 1: Print header image via CUPS and wait until done
# --------------------------------------------------
result = subprocess.run([
    "lp",
    "-d", "Star_TSP800_",
    "-o", "scaling=100",
    "-o", "fit-to-page",
    "-o", "orientation-requested=3",
    "logo3.jpeg"
], capture_output=True, text=True)

job_output = result.stdout.strip()
if not job_output:
    raise RuntimeError("Failed to submit logo print job")

# Example lp output: "request id is Star_TSP800_-12 (1 file(s))"
job_id = job_output.split(" ")[3]

# Wait until CUPS reports job is done
while True:
    stat = subprocess.run(
        ["lpstat", "-W", "not-completed"],
        capture_output=True,
        text=True
    ).stdout
    if job_id not in stat:
        break
    time.sleep(0.5)

print("✅ Logo finished printing, continuing with receipt text...")

# --------------------------------------------------
# STEP 2: Continue with ESC/POS raw printing
# --------------------------------------------------

# Find Star TSP800II
dev = usb.core.find(idVendor=0x0519, idProduct=0x0001)
if dev is None:
    raise ValueError("Printer not found")

# Detach kernel driver if necessary
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

# Set configuration
dev.set_configuration()

# Get endpoint
cfg = dev.get_active_configuration()
intf = cfg[(0,0)]
ep = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
)

# Printer initialization
ep.write(b'\x1b\x40')        # Initialize printer
ep.write(b'\x1b\x74\x01')    # Select UK character set (for £ symbol)

ep.write(b'\n' * 2)


# --------------------------------------------------
# COMPLETE HEADER
# --------------------------------------------------
ep.write(b'\x1b\x1d\x61\x01')     # Center alignment
ep.write(b'\x1b\x69\x00\x00')
ep.write(b'MEMBER of L.A.P.A.D.A and THE SILVER SOCIETY.\n')
ep.write(b'DEALERS IN FINE SILVER, SCOTTISH REGALIA, JEWELLERY AND CERAMICS\n\n')
ep.write(b'2 Aird House, High Street, Beauly, Scotland, IV4 7BS\n')
ep.write(b'Tel: 01463 782372   Info@iain-marr-antiques.com\n\n')
ep.write(b'\x1b\x1d\x61\x00')
ep.write(b'\n' * 2)

# --------------------------------------------------
# Functions
# --------------------------------------------------
def format_item(id, name, value, width):
    left = f"{id} - {name}"
    available_width = width - len(value) - 6
    wrapped = textwrap.wrap(left, available_width)
    output = []
    for i, line in enumerate(wrapped):
        if i == 0:
            spaces = width - len(line) - len(value) - 2
            if spaces < 1:
                spaces = 1
            output.append(line.encode("cp1252") + b" " * spaces + b"\xA3" + value.encode("cp1252"))
        else:
            output.append(line.encode("cp1252"))
    return output

def format_total_line(label, value, width):
    spaces = width - len(label) - len(value) - 2
    if spaces < 1:
        spaces = 1
    return label.encode('cp1252') + b' ' * spaces + b'\xA3' + value.encode('cp1252')

def print_line(label, value, bold=False):
    if bold:
        ep.write(b'\x1b\x45\x01')  # Bold ON
    ep.write(format_total_line(label, value, line_width) + b"\n")
    if bold:
        ep.write(b'\x1b\x45\x00')  # Bold OFF

# --------------------------------------------------
# Products
# --------------------------------------------------
selectedProducts = [
    {"id": "IMA1", "name": "Sultan is testing", "price": 451.00},
    {"id": "IMA2", "name": "2 items Silver coffee pot (27.5 ozs troy) and teapot (24oz troy). Maker Thomas Bradbury & Sons (Joseph & Edward Bradbury) London 1875.", "price": 1350.00},
    {"id": "IMA3", "name": "Scottish silver teapot Edinburgh 1876. Maker Mackays Chisholm 18oz Troy", "price": 945.00}
]

line_width = 68

for product in selectedProducts:
    for part in format_item(product["id"], product["name"], str(product["price"]), line_width):
        ep.write(part + b"\n")
    ep.write(b'\n')

# --------------------------------------------------
# Totals
# --------------------------------------------------
subtotal = sum(float(product["price"]) for product in selectedProducts)
vat = subtotal * 0.2
grand_total = subtotal + vat

print_line("Subtotal:", f"{subtotal:.2f}")
print_line("VAT (20%):", f"{vat:.2f}")
ep.write(b"\n")
print_line("GRAND TOTAL:", f"{grand_total:.2f}", bold=True)

# --------------------------------------------------
# Feed / Cut
# --------------------------------------------------
ep.write(b'\n' * 3)
ep.write(b'\x1b\x64\x02')  # Feed 2 lines
# ep.write(b'\x1d\x56\x41\x00')  # Uncomment for partial cut

usb.util.dispose_resources(dev)
