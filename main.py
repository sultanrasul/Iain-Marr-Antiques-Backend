from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Add this import
import os

import requests
import json

# Google Spread Sheet and Auth for the Stocks Spread Sheet
import gspread
from google.oauth2.service_account import Credentials

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

@app.route('/get_stock', methods=['POST'])
def get_stock():
    
    # Get all rows
    data = sheet.get_all_records()

    return jsonify(data)

@app.route('/print_labels', methods=['POST'])
def print_labels():
    data = request.json

    print(data)

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))