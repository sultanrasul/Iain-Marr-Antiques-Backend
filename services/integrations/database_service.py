import json
from typing import List, Tuple, Optional
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import settings
from gspread_formatting import *
import csv
import sqlite3
from collections import defaultdict

from schemas.printRequest import PrintRequest
from schemas.product import Product
from schemas.soldProduct import SoldProduct
from utils.timing import timeit

class DatabaseService:
    def __init__(self, db_path: str = "database.sqlite"):
        """
        Initialize the database service with a connection path.
        """
        self.db_path = db_path

        # Ensure the products table exists on init
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self.init_tables()
    
    def init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku_no TEXT UNIQUE NOT NULL,
                im_sku TEXT,
                description TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity >= -1),
                selling_price REAL NOT NULL CHECK(selling_price >= 0),
                purchase_price REAL,
                date_purchased DATE,
                "name/address_seller" TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                email TEXT,
                phone TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                date_sold DATE,
                invoice_no TEXT,
                total_amount REAL,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sold_products (
                sold_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        """)
        self.conn.commit()
        

    def import_products_to_db(self, products: List[Product]) -> List[Tuple[int, str]]:
        """
        Import Product instances into the existing `products` table.
        Returns a list of errors: (row_number, reason)
        """
        errors = []
        seen_skus = set()
        
        for product in products:
            sku = product.sku_no.strip()
            
            # Validate SKU
            if not sku:
                errors.append((product.row_number, "SKU is empty"))
                continue
            
            if sku in seen_skus:
                errors.append((product.row_number, f"Duplicate SKU in sheet: '{sku}'"))
                continue
            seen_skus.add(sku)
            
            try:
                self.cursor.execute("""
                INSERT INTO products (sku_no, im_sku, description, quantity, selling_price, purchase_price, date_purchased, "name/address_seller")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku_no) DO UPDATE SET
                    im_sku=excluded.im_sku,
                    description=excluded.description,
                    selling_price=excluded.selling_price,
                    purchase_price=excluded.purchase_price,
                    date_purchased=excluded.date_purchased,
                    "name/address_seller"=excluded."name/address_seller"
                """, (
                    sku,
                    product.im_sku,
                    product.item_description,
                    product.quantity,
                    product.selling_price,
                    product.purchase_price,
                    product.date_bought,
                    product.seller_name_address
                ))
            except Exception as e:
                errors.append((product.row_number, str(e)))
                continue
        
        self.conn.commit()
        return errors

    def import_sold_products_to_db(self, sold_products: List[SoldProduct]) -> List[Tuple[int, str]]:
        """
        Import SoldProduct instances into the database.
        Groups sold products by (date_sold, customer_name).
        """
        errors = []

        # Step 1: Group products by (date_sold, customer_name or 'anonymous')
        grouped_sales = defaultdict(list)
        for sold in sold_products:
            if not sold.date_sold:
                errors.append((sold.row_number, "Missing date_sold, cannot group"))
                continue
            key = (sold.date_sold, sold.customer_name or "")
            grouped_sales[key].append(sold)

        # Step 2: Insert grouped sales as orders
        for (date_sold, customer_name_key), products_in_order in grouped_sales.items():
            try:
                customer_id = None
                if customer_name_key != "":
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO customers (name)
                        VALUES (?)
                    """, (customer_name_key,))
                    self.cursor.execute("SELECT customer_id FROM customers WHERE name = ?", (customer_name_key,))
                    customer_id = self.cursor.fetchone()[0]

                # Sum total_price for the order
                total_amount = sum(p.selling_price for p in products_in_order)

                # Insert order
                self.cursor.execute("""
                    INSERT INTO orders (customer_id, date_sold, invoice_no, total_amount)
                    VALUES (?, ?, ?, ?)
                """, (customer_id, date_sold ,None, total_amount))
                order_id = self.cursor.lastrowid

                # Insert all items in this order
                for sold in products_in_order:
                    # Find product_id
                    self.cursor.execute("SELECT product_id FROM products WHERE sku_no = ?", (sold.sku_no,))
                    product_row = self.cursor.fetchone()
                    if not product_row:
                        errors.append((sold.row_number, f"SKU not found in products: {sold.sku_no}"))
                        continue
                    product_id = product_row[0]

                    # Insert order_item
                    self.cursor.execute("""
                        INSERT INTO sold_products (order_id, product_id, quantity)
                        VALUES (?, ?, ?)
                    """, (order_id, product_id, sold.quantity))

                    # Update product quantity
                    self.cursor.execute("""
                        UPDATE products
                        SET quantity = quantity - ?
                        WHERE product_id = ?
                    """, (sold.quantity, product_id))

            except Exception as e:
                for sold in products_in_order:
                    errors.append((sold.row_number, str(e)))
                continue

        self.conn.commit()
        return errors

