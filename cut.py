import usb.core, usb.util
import textwrap
import subprocess
import time

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

ep.write(b'\x1b\x64\x00')  # Feed 1 lines
ep.write(b'\x1d\x56\x41\x00')  # Partial cut

usb.util.dispose_resources(dev)
