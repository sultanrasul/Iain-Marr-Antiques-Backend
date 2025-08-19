import usb.core, usb.util

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
ep = usb.util.find_descriptor(intf, custom_match=lambda e: 
    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

# Printer initialization
ep.write(b'\x1b\x40')  # Initialize printer
ep.write(b'\x1b\x74\x01')  # Select UK character set (for £ symbol)

# --------------------------------------------------
# COMPLETE HEADER (As shown in logo.jpeg)
# --------------------------------------------------
ep.write(b'\x1b\x1d\x61\x01')     # Center alignment

# Company Name (Large)
ep.write(b'\x1b\x69\x01\x01')      # Double width & height
ep.write(b'IAIN MARR ANTIQUES\n')
ep.write(b'\x1b\x69\x00\x00')      # Normal text size

# Established Year
ep.write(b'ESTABLISHED 1975\n\n')

# Memberships
ep.write(b'MEMBER of L.A.P.A.D.A and THE SILVER SOCIETY.\n')

# Business Description
ep.write(b'DEALERS IN FINE SILVER, SCOTTISH REGALIA,JEWELLERY AND CERAMICS\n\n')

# Address
ep.write(b'2 Aird House, High Street, Beauly, Scotland, IV4 7BS\n')

# Contact Info
ep.write(b'  Tel:01463782372   Info@iain-marr-antiques.com  \n')

ep.write(b'\x1b\x1d\x61\x00')     # Left alignment (for rest of document)
ep.write(b'\n' * 2)                # Spacer before items

# --------------------------------------------------
# BODY ITEMS (With Consistent Spacing)
# --------------------------------------------------
items = [
    ("Antique Vase", "120.00"),
    ("Victorian Chair", "85.50"),
    ("Restoration Fee", "40.00"),
    ("Silver Candelabra (rare)", "350.00")
]

for item, price in items:
    # Left-aligned item with consistent spacing before price
    ep.write(item.encode('utf-8'))
    ep.write(b'    \x9C' + price.encode('utf-8') + b'\n')  # 4 spaces before £

ep.write(b'\n' * 2)  # Section spacer

# --------------------------------------------------
# FOOTER & TOTAL (With Same Spacing as Items)
# --------------------------------------------------
# Subtotal
ep.write(b'Subtotal:    \x9C595.50\n')  # 4 spaces

# VAT
ep.write(b'VAT (20%):    \x9C119.10\n\n')  # 4 spaces

# Grand Total (with emphasis)
ep.write(b'\x1b\x45\x01')          # Bold ON
ep.write(b'GRAND TOTAL:    \x9C714.60\n')  # 4 spaces
ep.write(b'\x1b\x45\x00')          # Bold OFF

# --------------------------------------------------
# FINAL SPACING & CUT
# --------------------------------------------------
ep.write(b'\n' * 3)                # Feed 3 lines
ep.write(b'\x1b\x64\x02')          # Feed 2 more lines
ep.write(b'\x1d\x56\x41\x00')      # Partial cut

# Release USB device
usb.util.dispose_resources(dev)