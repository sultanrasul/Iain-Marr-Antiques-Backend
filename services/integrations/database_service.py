import json
from typing import List, Tuple, Optional, Dict
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import settings
from gspread_formatting import *
import csv
import sqlite3
from collections import defaultdict
import re

from schemas.getSalesRequest import GetSalesRequest
from schemas.getStockRequest import GetStockRequest
from schemas.printRequest import PrintRequest
from schemas.product import Product
from schemas.soldProduct import SoldProduct
from utils.timing import timeit

class DatabaseService:
    def __init__(self, db_path: str = "database.sqlite"):
        """
        Initialize the database service with a connection path.
        """
        self.db_path = settings.DATABASE_PATH
        
        # Ensure the products table exists on init
        self.conn = sqlite3.connect(self.db_path)
        
        self.conn.row_factory = sqlite3.Row

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

                -- snapshot fields
                description TEXT NOT NULL,
                sku_no TEXT,
                im_sku TEXT,
                selling_price REAL NOT NULL CHECK(selling_price >= 0),

                quantity INTEGER,
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        """)
        self.conn.commit()
    @timeit
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

    @timeit
    def import_sold_products_to_db(self, sold_products: List[SoldProduct]) -> List[Tuple[int, str]]:
        errors: List[Tuple[int, str]] = []

        # Reset tables (safe because we now trust sheet order_id)
        self.cursor.execute("DELETE FROM sold_products")
        self.cursor.execute("DELETE FROM orders")

        grouped_sales: Dict[int, List[SoldProduct]] = defaultdict(list)

        # Group rows by ORDER ID from sheet
        for sold in sold_products:

            if not sold.order_id:
                errors.append((sold.row_number, "Missing order_id"))
                continue

            if not sold.date_sold:
                errors.append((sold.row_number, "Missing date_sold"))
                continue

            grouped_sales[sold.order_id].append(sold)

        # Create orders
        for sheet_order_id, products in grouped_sales.items():

            first = products[0]
            date_sold = first.date_sold
            customer_name = first.customer_name
            invoice_no = first.invoice_no_xero

            customer_id = None

            if customer_name:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO customers (name) VALUES (?)",
                    (customer_name,)
                )

                self.cursor.execute(
                    "SELECT customer_id FROM customers WHERE name = ?",
                    (customer_name,)
                )

                result = self.cursor.fetchone()
                if result:
                    customer_id = result[0]

            total_amount = sum(p.selling_price * p.quantity for p in products)

            # ✅ Use ORDER ID from sheet (NOT lastrowid)
            self.cursor.execute("""
                INSERT OR REPLACE INTO orders (order_id, customer_id, date_sold, invoice_no, total_amount)
                VALUES (?, ?, ?, ?, ?)
            """, (sheet_order_id, customer_id, date_sold, invoice_no, total_amount))

            # Insert order items
            for sold in products:
                self.cursor.execute(
                    "SELECT product_id, quantity FROM products WHERE sku_no = ?",
                    (sold.sku_no,)
                )

                row = self.cursor.fetchone()

                if not row:
                    errors.append((sold.row_number, f"SKU not found: {sold.sku_no}"))
                    continue

                product_id, current_qty = row

                self.cursor.execute("""
                    INSERT INTO sold_products (order_id, product_id, description, sku_no, im_sku, selling_price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sheet_order_id, product_id,sold.item_description, sold.sku_no, sold.im_sku, sold.selling_price, sold.quantity))

                new_qty = max(current_qty - sold.quantity, 0)

                self.cursor.execute("""
                    UPDATE products
                    SET quantity = ?
                    WHERE product_id = ?
                """, (new_qty, product_id))

        self.conn.commit()

        return errors

    def get_stock(self, request: GetStockRequest):
        # Map frontend sort fields to actual DB columns
        sort_mapping = {
            "sku_no": "product_id",  # sort by product_id when frontend says sku_no
            "im_sku": "im_sku",
            "description": "description",
            "quantity": "quantity",
            "selling_price": "selling_price",
            "purchase_price": "purchase_price"
        }

        # Determine the column to sort by
        sort_field = sort_mapping.get(request.sort_field, "im_sku")
        sort_order = request.sort_order if request.sort_order in ["asc", "desc"] else "desc"

        # Pagination parameters from frontend
        use_pagination = request.page and request.items_per_page
        if use_pagination:
            page = request.page if request.page > 0 else 1
            items_per_page = request.items_per_page
            offset = (page - 1) * items_per_page
        else:
            page = None
            items_per_page = None
            offset = None

        query = f"""
            SELECT *,
                CASE WHEN quantity = 0 THEN 1 ELSE 0 END AS sold
            FROM products
            WHERE (:sku_text IS NULL OR sku_no LIKE :sku_text OR im_sku LIKE :sku_text)
            AND (:description IS NULL OR description LIKE :description)
            AND (:min_selling_price IS NULL OR selling_price >= :min_selling_price)
            AND (:min_purchase_price IS NULL OR purchase_price >= :min_purchase_price)
            ORDER BY {sort_field} {sort_order}
        """
        if use_pagination:
            query += "\nLIMIT :limit OFFSET :offset"


        params = {
            "sku_text": f"%{request.sku_text}%" if request.sku_text else None,
            "description": f"%{request.description}%" if request.description else None,
            "min_selling_price": request.min_selling_price,
            "min_purchase_price": request.min_purchase_price
        }
        if use_pagination:
            params["limit"] = items_per_page
            params["offset"] = offset

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        return [Product.from_db_row(dict(row)) for row in rows]
        
    def get_sales(self, request: GetSalesRequest):
        
        SORT_FIELD_MAP = {
            "order_id": "o.order_id",
            "customer_name": "c.name",
            "date_sold": "o.date_sold",
            "total_amount": "o.total_amount",
            "items_purchased": "items_purchased"  # alias from SELECT
        }

        sort_field = SORT_FIELD_MAP.get(request.sort_field, "o.order_id")
        sort_order = request.sort_order or "asc"

        # Pagination parameters from frontend
        use_pagination = request.page and request.items_per_page
        if use_pagination:
            page = request.page if request.page > 0 else 1
            items_per_page = request.items_per_page
            offset = (page - 1) * items_per_page
        else:
            page = None
            items_per_page = None
            offset = None
            
        query = f"""
            SELECT 
                o.order_id,
                c.name AS customer_name,
                o.date_sold,
                o.total_amount,
                COALESCE(SUM(sp.quantity), 0) AS items_purchased
            FROM orders o
            LEFT JOIN customers c
                ON o.customer_id = c.customer_id
            LEFT JOIN sold_products sp
                ON sp.order_id = o.order_id
            WHERE
                (:order_id IS NULL OR o.order_id = :order_id)
                AND (:customer_id IS NULL OR o.customer_id = :customer_id)
                AND (:customer_name IS NULL OR c.name LIKE :customer_name)
                AND (:date_from IS NULL OR o.date_sold >= :date_from)
                -- Adjust :date_to to include the entire day if specified
                AND (:date_to IS NULL OR o.date_sold <= datetime(:date_to, '+1 day', '-1 second'))
            GROUP BY 
                o.order_id, c.name, o.date_sold, o.total_amount
            HAVING
                (:min_items IS NULL OR COALESCE(SUM(sp.quantity), 0) >= :min_items)
                AND (:min_price IS NULL OR o.total_amount >= :min_price)
            ORDER BY {sort_field} {sort_order}
        """

        if use_pagination:
            query += "\nLIMIT :limit OFFSET :offset"

        params = {
            "order_id": request.order_id,
            "customer_id": request.customer_id,
            "customer_name": f"%{request.customer_name}%" if request.customer_name else None,
            "date_from": request.date_from,
            "date_to": request.date_to,
            "min_items": request.min_items,
            "min_price": request.min_price
        }
        if use_pagination:
            params["limit"] = items_per_page
            params["offset"] = offset

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_order_products(self, order_id: str) -> List[Product]:
        self.cursor.execute(
        """
            -- Get a list of products by order id
            SELECT 
                p.product_id,
                sp.sku_no,
                sp.im_sku,
                sp.description,
                sp.quantity,
                sp.selling_price
            FROM sold_products sp
            INNER JOIN products p
                ON sp.product_id = p.product_id
            WHERE order_id = ?;
        """, (order_id,))
        rows = self.cursor.fetchall()

        return [Product.from_db_row(dict(row)) for row in rows]

    def add_product(self, product: Product) -> Optional[str]:
        try:
            self.cursor.execute("""
                INSERT INTO products (
                    sku_no,
                    im_sku,
                    description,
                    quantity,
                    selling_price,
                    purchase_price,
                    date_purchased,
                    "name/address_seller"
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.new_sku_no.strip(),
                product.im_sku,
                product.item_description,
                product.quantity,
                product.selling_price,
                product.purchase_price,
                product.date_bought,
                product.seller_name_address
            ))

            self.conn.commit()
            return None

        except sqlite3.IntegrityError as e:
            error_message = str(e)
            if "UNIQUE constraint failed" in error_message:
                return "SKU number already exists"

            if "NOT NULL constraint failed" in error_message:
                return "A required field is missing"

            return error_message

        except Exception as e:
            return str(e)
    
    @timeit
    def modify_product(self, product: Product) -> Optional[str]:
        try:
            self.cursor.execute("""
                UPDATE products
                SET
                    sku_no = ?,
                    im_sku = ?,
                    description = ?,
                    quantity = ?,
                    selling_price = ?,
                    purchase_price = ?,
                    date_purchased = ?,
                    "name/address_seller" = ?
                WHERE sku_no = ?
            """, (
                product.new_sku_no.strip(),          # NEW sku_no
                product.im_sku,
                product.item_description,
                product.quantity,
                product.selling_price,
                product.purchase_price,
                product.date_bought,
                product.seller_name_address,
                product.sku_no.strip()               # OLD sku_no
            ))

            if self.cursor.rowcount == 0:
                return "Product not found"

            self.conn.commit()
            return None

        except Exception as e:
            error_message = str(e)
            print(F"ERROR: {error_message}")
            if "UNIQUE constraint failed" in error_message:
                return "SKU number already exists. Please use a different SKU."

            if "NOT NULL constraint failed" in error_message:
                return "A required field is missing."

            return error_message
    
    def add_sold_product(self, printRequest: PrintRequest) -> Optional[str]:
        try:
            
            # If not marking as sold, do nothing DB-related
            if not printRequest.mark_as_sold:
                return None

            self.conn.execute("BEGIN")

            customer_id = None

            # 1. Handle customer
            if printRequest.customer_name:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO customers (name, email) VALUES (?, ?)",
                    (printRequest.customer_name, printRequest.email_address)
                )

                self.cursor.execute(
                    "SELECT customer_id FROM customers WHERE name = ?",
                    (printRequest.customer_name,)
                )

                row = self.cursor.fetchone()
                if row:
                    customer_id = row["customer_id"]

            # 2. Calculate total and getting quantity of old product
            total_amount = 0
            product_rows = []

            for item in printRequest.products:
                self.cursor.execute(
                    "SELECT product_id, quantity, selling_price FROM products WHERE sku_no = ?",
                    (item.sku_no,)
                )

                row = self.cursor.fetchone()

                if not row:
                    self.conn.rollback()
                    return f"SKU not found: {item.sku_no}"

                product_id = row["product_id"]
                current_qty = row["quantity"]
                selling_price = row["selling_price"]

                # Default quantity = 1 if not provided
                qty_to_sell = max(1,item.quantity if item.quantity is not None else 1)

                total_amount += selling_price * qty_to_sell

                product_rows.append((product_id, current_qty, qty_to_sell))

            # 3. Create order
            self.cursor.execute("""
                INSERT INTO orders (customer_id, date_sold, invoice_no, total_amount)
                VALUES (?, ?, ?, ?)
            """, (
                customer_id,
                printRequest.date_sold,
                None,  # No invoice_no in PrintRequest
                total_amount
            ))

            order_id = self.cursor.lastrowid

            # 4. Insert sold_products + update stock
            for product_id, current_qty, qty_to_sell in product_rows:

                self.cursor.execute("""
                    INSERT INTO sold_products (order_id, product_id, quantity)
                    VALUES (?, ?, ?)
                """, (order_id, product_id, qty_to_sell))

                # Update quantity in products table
                new_qty = max(0, current_qty - qty_to_sell)

                self.cursor.execute("""
                    UPDATE products
                    SET quantity = ?
                    WHERE product_id = ?
                """, (new_qty, product_id))

            self.conn.commit()
            return order_id

        except Exception as e:
            self.conn.rollback()
            return str(e)

    def get_table_stats(self):
        query = """
            SELECT
                (SELECT COUNT(*) FROM products) AS total_products,
                (SELECT COUNT(*) FROM orders) AS total_orders,
                (SELECT COUNT(*) FROM sold_products) AS total_sales_rows,
                (SELECT COALESCE(SUM(quantity), 0) FROM sold_products) AS total_items_sold,
                (SELECT COALESCE(SUM(total_amount), 0) FROM orders) AS total_revenue,
                (SELECT COUNT(DISTINCT product_id) FROM sold_products) AS unique_products_sold
        """

        self.cursor.execute(query)
        row = self.cursor.fetchone()

        return dict(row)
    
    def get_next_sku_num(self) -> str:
        """
        Generate the next SKU number by incrementing the numeric part.
        Pattern: 2-999 → 3-0 → 3-1 → ... → 3-999 → 4-0 ...
        Ignores any trailing letters or spaces after the number.
        
        Raises:
            ValueError: if the next SKU already exists in the database.
        """
        # Get the last SKU by product_id
        self.cursor.execute("SELECT sku_no FROM products ORDER BY product_id DESC LIMIT 1")
        last_row = self.cursor.fetchone()

        if not last_row or not last_row["sku_no"]:
            # Start from 2-999 if no products yet
            next_sku = "2-999"
        else:
            last_sku = last_row["sku_no"].strip()
            try:
                # Split by dash
                prefix_str, num_part = last_sku.split("-", 1)
                prefix = int(prefix_str)

                # Extract the leading number from the second part, ignore letters/spaces
                match = re.match(r"(\d+)", num_part.strip())
                if match:
                    num = int(match.group(1))
                else:
                    num = 0  # fallback if no number found

                if num < 999:
                    next_num = num + 1
                    next_sku = f"{prefix}-{next_num}"
                else:
                    next_sku = f"{prefix + 1}-0"
            except Exception:
                # Fallback if SKU format is completely invalid
                next_sku = "2-999"

        # Check if SKU already exists
        self.cursor.execute("SELECT 1 FROM products WHERE sku_no = ?", (next_sku,))
        if self.cursor.fetchone():
            raise ValueError(f"Next SKU '{next_sku}' already exists in the database!")

        return next_sku

