from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Add this import
import os

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

    receipt_header()


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
def receipt_header():
    # Printer initialization
    printer.write(b'\x1b\x40')  # Initialize printer
    printer.write(b'\x1b\x74\x01')  # Select UK character set (for £ symbol)

    # --------------------------------------------------
    # COMPLETE HEADER (As shown in logo.jpeg)
    # --------------------------------------------------
    printer.write(b'\x1b\x1d\x61\x01')     # Center alignment

    # Company Name (Large)
    printer.write(b'\x1b\x69\x01\x01')      # Double width & height
    printer.write(b'IAIN MARR ANTIQUES\n')
    printer.write(b'\x1b\x69\x00\x00')      # Normal text size

    # Established Year
    printer.write(b'ESTABLISHED 1975\n\n')

    # Memberships
    printer.write(b'MEMBER of L.A.P.A.D.A and THE SILVER SOCIETY.\n')

    # Business Description
    printer.write(b'DEALERS IN FINE SILVER, SCOTTISH REGALIA,JEWELLERY AND CERAMICS\n\n')

    # Address
    printer.write(b'2 Aird House, High Street, Beauly, Scotland, IV4 7BS\n')

    # Contact Info
    printer.write(b'  Tel:01463782372   Info@iain-marr-antiques.com  \n')

    printer.write(b'\x1b\x1d\x61\x00')     # Left alignment (for rest of document)
    printer.write(b'\n' * 2)                # Spacer before items



    printer.write(b'\x1b\x64\x02')          # Feed 2 more lines
    printer.write(b'\x1d\x56\x41\x00')      # Partial cut


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))