from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Add this import
import os

import textwrap
import subprocess
import time
from datetime import datetime
from send_email import send_email


import requests
import json

# Google Spread Sheet and Auth for the Stocks Spread Sheet
import gspread
from google.oauth2.service_account import Credentials

# Printer
import usb.core, usb.util

from dotenv import load_dotenv
load_dotenv()

# Path to your service account key JSON
# SERVICE_ACCOUNT_FILE = "iain-marr-antiques-04d650544d22.json"

# Load JSON from environment variable
SERVICE_ACCOUNT_FILE = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

# Define the scope for spreadsheet
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate Service Account
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
# Connect to Google Sheets
client = gspread.authorize(creds)


# Start Flask
app = Flask(__name__)
CORS(app, origins="*")  # Add CORS support


# workbook = client.open_by_key("18OnhVvM-2JBY7xE-Yd7Gft99kX4uSnp0PAY7t1Z4wYw") Actual Sheet
workbook = client.open_by_key("1ZzFR06jqHqJk3EwVYPCJn8VUeu7Zsty8N_uLvlH1pW8") # Test Sheet
items = workbook.sheet1
sold_items = workbook.get_worksheet(1)  # index starts at 0

dev = None
printer = None


def try_connect_printer():
    # Try to connect to the printer. Return True if connected.
    global dev, printer
    try:
        dev = usb.core.find(idVendor=0x0519, idProduct=0x0001)
        if dev is None:
            printer = None
            return False

        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)

        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]
        printer = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        return printer is not None
    except Exception as e:
        dev = None
        printer = None
        return False
    
try_connect_printer()

@app.route("/reconnect_printer", methods=["GET"])
def reconnect_printer():
    connected = try_connect_printer()
    return jsonify({"connected": connected})

# Restart Raspberry Pi
@app.route("/restart", methods=["POST"])
def restart_pi():
    try:
        # Schedule a restart after 1 second
        subprocess.Popen(["sudo", "shutdown", "-r", "now"])
        return jsonify({"success": True, "message": "Raspberry Pi is restarting..."}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Shutdown Raspberry Pi
@app.route("/shutdown", methods=["POST"])
def shutdown_pi():
    try:
        # Schedule a shutdown after 1 second
        subprocess.Popen(["sudo", "shutdown", "now"])
        return jsonify({"success": True, "message": "Raspberry Pi is shutting down..."}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_stock", methods=["POST"])
def get_stock():
    # existing logic
    data = items.get_all_records()
    printer_connected = printer is not None
    return jsonify({
        "data": data,
        "printer_connected": try_connect_printer()
    })

@app.route('/print_labels', methods=['POST'])
def print_labels():
    data = request.json
    selected_products = data.get("selectedProducts", [])
    customer = data.get("customerName", "")
    emailReceipt = data.get("emailReceipt", False)
    emailAddress = data.get("emailAddress", "")

    # paymentType = data.get("paymentType", "")
    duplicateCount = data.get("duplicateCount", 1)
    logSold = data.get("logSold", False)


    if try_connect_printer() == False and duplicateCount !=0:
        return jsonify({"success": False, "error": "Printer not connected"}), 400
    
    for i in range(duplicateCount):
        # print(f"Print {i+1}")
        print_receipt(selected_products, customer)

    send_email(selected_products=selected_products, customer=customer, emailAddress=emailAddress)

    if logSold:

        all_records = items.get_all_records()
        headers = items.row_values(1)

        for product in selected_products:
            sku = str(product.get("sku")).strip()
            row_index = None

            # Find row in Items
            for i, record in enumerate(all_records, start=2):  # start=2 because header is row 1
                if str(record.get("SKU NO.")).strip() == sku:
                    row_index = i
                    break

            if not row_index:
                continue  # skip if SKU not found

            # Normal row for Items (no customer field here)
            updated_row = [
                product.get("sku", ""),
                product.get("imSKU", ""),
                product.get("name", ""),
                product.get("price", ""),
                product.get("dateBought", ""),
                product.get("seller", ""),
                product.get("purchasePrice", ""),
                product.get("commission", ""),
                datetime.now().strftime("%-d.%-m.%y %H:%M"),  
                # datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # use this when the column is changed to datetime in sheets
                product.get("invoiceNo", ""),
                True if product.get("onWebsite") else "",
                product.get("location", ""),
                True  # sold
            ]

            # Update in Items sheet
            items.update(
                [updated_row],
                range_name=f"A{row_index}:{chr(64 + len(headers))}{row_index}"
            )

            sold_row = [
                product.get("sku", ""),
                product.get("imSKU", ""),
                customer,  # insert customer here
                product.get("name", ""),
                product.get("price", ""),
                product.get("dateBought", ""),
                product.get("seller", ""),
                product.get("purchasePrice", ""),
                product.get("commission", ""),
                datetime.now().strftime("%-d.%-m.%y %H:%M"),  
                # datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # use this when the column is changed to datetime in sheets
                # paymentType,
                product.get("invoiceNo", ""),
                True if product.get("onWebsite") else "",
                product.get("location", ""),
                True
            ]
            sold_items.append_row(sold_row, value_input_option="USER_ENTERED")

    return jsonify({
        "success": True,
        "sold_count": len(selected_products) if logSold else 0,
        "printed_count": len(selected_products)
    })


@app.route('/modify_product', methods=['POST'])
def modify_product():
    data = request.json.get("editedProduct", {})
    sku = data.get("sku")

    if not sku:
        return jsonify({"error": "SKU is required"}), 400

    # Get all rows
    all_records = items.get_all_records()
    
    # Find the row index (gspread is 1-indexed, plus header row)
    row_index = None
    for i, record in enumerate(all_records, start=2):  # start=2 because row 1 is header
        if str(record.get("SKU NO.")).strip() == str(sku).strip():
            row_index = i
            break

    if not row_index:
        return jsonify({"error": "SKU not found"}), 404

    # Prepare updated row values in the same order as the spreadsheet headers
    headers = items.row_values(1)
    updated_row = [
        data.get("sku", ""),
        data.get("imSKU", ""),
        data.get("name", ""),
        data.get("price", ""),
        data.get("dateBought", ""),
        data.get("seller", ""),
        data.get("purchasePrice", ""),
        data.get("commission", ""),
        data.get("dateSold", ""),
        data.get("invoiceNo", ""),
        True if data.get("onWebsite") else "",
        data.get("location", ""),
        True if data.get("sold") else False
    ]

    # Update the row
    items.update(f"A{row_index}:{chr(64 + len(headers))}{row_index}", [updated_row])

    return jsonify({"success": True, "updated_row": updated_row})

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json.get("product", {})

    # Prepare new row in the same order as your sheet headers
    new_row = [
        data.get("sku", ""),
        data.get("imSKU", ""),
        data.get("name", ""),
        data.get("price", ""),
        data.get("dateBought", ""),
        data.get("seller", ""),
        data.get("purchasePrice", ""),
        data.get("commission", ""),
        data.get("dateSold", ""),
        data.get("invoiceNo", ""),
        True if data.get("onWebsite") else "",
        data.get("location", ""),
        True if data.get("sold") else False
    ]

    # Append to the sheet
    items.append_row(new_row, value_input_option="USER_ENTERED")

    return jsonify({"success": True, "new_row": new_row})

# Printer Functions
def print_receipt(selectedProducts, customerName):
    # Printer width for 112mm
    line_width = 68


    # --------------------------------------------------
    # PRINT HEADER
    # --------------------------------------------------

    result = subprocess.run([
        "lp",
        "-d", "Star_TSP800_",
        "-o", "scaling=100",
        "-o", "fit-to-page",
        "-o", "orientation-requested=3",
        "/home/sultanrasul/backend/header.jpeg"
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

    # Printer initialization
    printer.write(b'\x1b\x40')        # Initialize printer
    printer.write(b'\x1b\x74\x01')    # Select UK character set (for £ symbol)
    printer.write(b'\n')



    # --------------------------------------------------
    # SECOND HALF HEADER
    # --------------------------------------------------
    # printer.write(b'\x1b\x1d\x61\x01')     # Center alignment
    # printer.write(b'\x1b\x69\x00\x00')
    # printer.write(b'MEMBER of L.A.P.A.D.A and THE SILVER SOCIETY.\n')
    # printer.write(b'DEALERS IN FINE SILVER, SCOTTISH REGALIA, JEWELLERY AND CERAMICS\n\n')
    # printer.write(b'2 Aird House, High Street, Beauly, Scotland, IV4 7BS\n')
    # printer.write(b'Tel: 01463 782372   Info@iain-marr-antiques.com\n\n')


    printer.write(b'\x1b\x1d\x61\x00')
    printer.write(b'\n')

    # Function for printing items with text wrapping
    def format_item(id, name, value, width, longestID):
        """Prints item with aligned ids, wraps long names across lines."""
        # Pad ID so that all dashes line up
        print(f"Longest ID: {longestID}")
        padding = " " * (longestID - len(str(id)) )
        print(f"Padding: {padding}")

        prefix = f"{str(id)}{padding} - "

        left = f"{prefix}{name}"

        # Calculate available space for text (accounting for price)
        available_width = width - len(value) - 6  # -3 for " £" and space

        # Wrap the label into lines, indenting subsequent lines to align after prefix
        wrapped = textwrap.wrap(
            left,
            available_width,
            subsequent_indent=" " * len(prefix)
        )

        output = []
        for i, line in enumerate(wrapped):
            if i == 0:
                # First line gets the price, right aligned
                spaces = width - len(line) - len(value) - 2  # -2 for "£" and space
                if spaces < 1:
                    spaces = 1
                output.append(line.encode("cp1252") + b" " * spaces + b"\xA3" + value.encode("cp1252"))
            else:
                # Continuation lines already have correct indent
                output.append(line.encode("cp1252"))
        return output
    
    # Function for aligned totals (no wrapping needed)
    def format_total_line(label, value, width, currency=True):
        """Format line with left-aligned label and right-aligned value (optionally prefixed with £)."""
        spaces = width - len(label) - len(value) - (2 if currency else 1)
        if spaces < 1:
            spaces = 1

        if currency:
            return label.encode('cp1252') + b' ' * spaces + b'\xA3' + value.encode('cp1252')
        else:
            return label.encode('cp1252') + b' ' * spaces + value.encode('cp1252')


    def print_line(label, value, bold=False, currency=True):
        if bold:
            printer.write(b'\x1b\x45')  # Bold ON
        printer.write(format_total_line(label, value, line_width, currency) + b"\n")
        printer.write(b'\x1b\x46')  # Bold OFF

    today = datetime.now().strftime("%-d.%-m.%y")  # e.g. "9.4.25"
    if len(customerName) > 0:
        print_line(f"Sold To: {customerName}", f"Date: {today}", currency=False, bold=True)
    else:
        print_line("", f"Date: {today}", currency=False, bold=True)

    printer.write(b"\n\n")


    longestID = max(len(str(product["id"])) for product in selectedProducts)
    for product in selectedProducts:
        for part in format_item(product["id"], product["name"], f"{product['price']:.2f}", line_width, longestID):
            printer.write(part + b"\n")
        printer.write(b'\n')

    # --------------------------------------------------
    # Totals
    # --------------------------------------------------
    # Calculate actual totals based on items
    total = sum(float(product["price"]) for product in selectedProducts)
    subtotal = total

    print_line("Subtotal:", f"{subtotal:.2f}")
    print_line("TOTAL:", f"{total:.2f}", bold=True)

    printer.write(b"\n\n")

    printer.write(b"VAT Reg No. 2965 743 08\n")
    printer.write(b"VAT has not been charged on the above items.")

    # --------------------------------------------------
    # Cut
    # --------------------------------------------------
    printer.write(b'\n' * 2)


    printer.write(b'\x1b\x64\x02')  # Feed 2 lines


    usb.util.dispose_resources(dev)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))