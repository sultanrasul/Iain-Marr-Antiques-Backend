# 🏺 Iain Marr Antiques Inventory & Receipt System (Backend)

> Developed end-to-end by **Sultan Rasul** as a freelance project for a local antique store.

🔗 **Frontend Repository:** [Iain Marr Antiques (Svelte Frontend)](https://github.com/sultanrasul/Iain-Marr-Antiques-Frontend)

---

## 🧩 Project Summary

### **Problem**
The store’s entire sales process was manual — handwritten receipts, stock updates in Apple Numbers, and no reliable digital record of transactions.  
There was no way to automatically log sales data or connect receipt printing with inventory management.

### **Solution**
Developed a **Flask-based backend** deployed on a **Raspberry Pi**, responsible for handling all server-side logic and hardware communication.  
Key functionality included:
- Secure **Google Sheets API** integration for retrieving and updating live stock data  
- **ESC/POS thermal printer control** via Linux CUPS to generate branded receipts directly from the POS  
- **Local REST API endpoints** for printing, adding, and modifying inventory, and system management (shutdown/restart)  

### **Impact**
Automated the store’s entire sales pipeline, transforming a slow, handwritten process into a seamless digital system.  
Reduced transaction time by over 50%, eliminated duplicate record-keeping, and provided reliable, structured data for business tracking.

---

## 🧠 Overview

This backend handles:
- Real-time inventory retrieval and search via Google Sheets API  
- USB receipt printing (112mm) using raw ESC/POS commands and CUPS on a Raspberry Pi  
- Transaction logging into Google Sheets for clean digital records  
- Management endpoints for adding, modifying, or selling products  
- Printer and Raspberry Pi control endpoints (reconnect, shutdown, restart)  

The frontend is built with **Svelte** and communicates with this backend via HTTP requests.

---

## 🏠 Google Sheets & Inventory Setup

The backend connects to a **Google Sheet** containing all store stock using a **service account**.  

To use your own sheet for testing or development:

1. Create a **Google service account** and download the JSON key.  
2. Update `SERVICE_ACCOUNT_FILE` in the backend code to point to your key.  
3. Share your sheet with the service account email.  

> ⚠️ Do **not** commit your JSON credentials — they must remain private.

---

## 💰 Receipt Printing & Automation

- Receipts print to a **112mm USB printer** connected to a Raspberry Pi running Linux CUPS.  
- Header/logo image is printed first, followed by dynamically formatted product lines, totals, and optional customer information.  
- ESC/POS commands are used for text formatting, alignment, and cutting.  
- Transactions are optionally logged into a second sheet automatically, eliminating handwritten records.

---

## ⚙️ Setup Instructions

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the environment
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 3. Install dependencies
pip install -r requirements.txt
```

---

The backend runs on http://localhost:8080
 by default.

Key endpoints:
- `POST /get_stock` → Retrieve inventory data
- `POST /print_labels` → Print receipts and optionally log sales
- `POST /add_product` → Add new stock
- `POST /modify_product` → Edit existing stock
- `POST /shutdown` → Shutdown Raspberry Pi
- `POST /restart` → Restart Raspberry Pi

---

## 🧰 Tech Stack
- Backend: Python, Flask, Flask-CORS
- Inventory/Database: Google Sheets via gspread API
- Printer Integration: USB printer via ESC/POS commands and Linux CUPS

Frontend: Svelte (separate repository)

Deployment: Raspberry Pi, local network
