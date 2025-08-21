from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Add this import
import os

import textwrap
import subprocess
import time

import requests
import json

# Google Spread Sheet and Auth for the Stocks Spread Sheet
import gspread
from google.oauth2.service_account import Credentials

# Printer
import usb.core, usb.util

# Path to your service account key JSON
SERVICE_ACCOUNT_FILE = "iain-marr-antiques-04d650544d22.json"

# Define the scope for spreadsheet
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate Service Account
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
# Connect to Google Sheets
client = gspread.authorize(creds)


# Start Flask
app = Flask(__name__)
CORS(app, origins="*")  # Add CORS support

# Open by name or URL
sheet = client.open_by_key("18OnhVvM-2JBY7xE-Yd7Gft99kX4uSnp0PAY7t1Z4wYw").sheet1


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
printer = usb.util.find_descriptor(intf, custom_match=lambda e: 
    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)


@app.route('/get_stock', methods=['POST'])
def get_stock():
    
    # Get all rows
    data = sheet.get_all_records()

    return jsonify(data)

@app.route('/print_labels', methods=['POST'])
def print_labels():
    data = request.json

    print_receipt(data["selectedProducts"])
    

    print(data)

    return jsonify(data)

@app.route('/modify_product', methods=['POST'])
def modify_product():
    data = request.json.get("editedProduct", {})
    sku = data.get("sku")

    if not sku:
        return jsonify({"error": "SKU is required"}), 400

    # Get all rows
    all_records = sheet.get_all_records()
    
    # Find the row index (gspread is 1-indexed, plus header row)
    row_index = None
    for i, record in enumerate(all_records, start=2):  # start=2 because row 1 is header
        if str(record.get("SKU NO.")).strip() == str(sku).strip():
            row_index = i
            break

    if not row_index:
        return jsonify({"error": "SKU not found"}), 404

    # Prepare updated row values in the same order as the spreadsheet headers
    headers = sheet.row_values(1)
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
    sheet.update(f"A{row_index}:{chr(64 + len(headers))}{row_index}", [updated_row])

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
    sheet.append_row(new_row, value_input_option="USER_ENTERED")

    return jsonify({"success": True, "new_row": new_row})

# Printer Functions
def print_receipt(selectedProducts):
    # Printer width for 112mm
    line_width = 68


    # --------------------------------------------------
    # FIRST HALF HEADER
    # --------------------------------------------------

    result = subprocess.run([
        "lp",
        "-d", "Star_TSP800_",
        "-o", "scaling=100",
        "-o", "fit-to-page",
        "-o", "orientation-requested=3",
        "/home/sultanrasul/backend/Final/logo.jpeg"
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

    result = subprocess.run([
        "lp",
        "-d", "Star_TSP800_",
        "-o", "scaling=100",
        "-o", "fit-to-page",
        "-o", "orientation-requested=3",
        "/home/sultanrasul/backend/Final/para.jpeg"
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
    printer.write(b'\n' * 2)



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
    def format_item(id, name, value, width):
        """Prints item with id + name, wraps long names across lines."""
        left = f"{id} - {name}"
        # Calculate available space for text (accounting for price)
        available_width = width - len(value) - 6  # -3 for " £" and space
        
        # Wrap the label into lines
        wrapped = textwrap.wrap(left, available_width)
        
        output = []
        for i, line in enumerate(wrapped):
            if i == 0:
                # First line gets the price
                # More precise calculation
                spaces = width - len(line) - len(value) - 2  # -2 for "£" and space
                if spaces < 1:
                    spaces = 1
                output.append(line.encode("cp1252") + b" " * spaces + b"\xA3" + value.encode("cp1252"))
            else:
                # Continuation lines, just left aligned
                output.append(line.encode("cp1252"))
        return output

    # Function for aligned totals (no wrapping needed)
    def format_total_line(label, value, width):
        """Format line with left-aligned label and right-aligned £value"""
        # More precise calculation
        spaces = width - len(label) - len(value) - 2  # -2 for "£" and space
        if spaces < 1:
            spaces = 1
        return label.encode('cp1252') + b' ' * spaces + b'\xA3' + value.encode('cp1252')

    def print_line(label, value, bold=False):
        if bold:
            printer.write(b'\x1b\x45\x01')  # Bold ON
        printer.write(format_total_line(label, value, line_width) + b"\n")
        if bold:
            printer.write(b'\x1b\x45\x00')  # Bold OFF


    for product in selectedProducts:
        for part in format_item(product["id"], product["name"], f"{product['price']:.2f}", line_width):
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
    printer.write(b"\n")

    # --------------------------------------------------
    # Cut
    # --------------------------------------------------
    printer.write(b'\n' * 2)

    # THIS IS THE VA WHAT IT IS PRINTING OUT
    printer.write(b'\x1b\x64\x02')  # Feed 2 lines


    usb.util.dispose_resources(dev)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))