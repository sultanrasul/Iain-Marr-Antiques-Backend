import usb.core
import usb.util

def list_usb_devices():
    devices = usb.core.find(find_all=True)

    results = []

    for dev in devices:
        try:
            vendor_id = hex(dev.idVendor)
            product_id = hex(dev.idProduct)

            manufacturer = usb.util.get_string(dev, dev.iManufacturer) or "Unknown"
            product = usb.util.get_string(dev, dev.iProduct) or "Unknown"

            name = f"{manufacturer} - {product}"

            results.append({
                "name": name,
                "vendor_id": dev.idVendor,
                "product_id": dev.idProduct
            })

        except Exception:
            continue

    return results

for device in list_usb_devices():
    print(device)