-- Enable foreign key enforcement
PRAGMA foreign_keys = ON;

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_no TEXT UNIQUE NOT NULL,                -- cannot be NULL
    im_sku TEXT,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= -1),
    selling_price REAL NOT NULL CHECK(selling_price >= 0),  -- optional: price >= 0
    purchase_price REAL,
    date_purchased DATE,
    "name/address_seller" TEXT
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    date_sold DATE,
    invoice_no TEXT,
    total_amount REAL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE sold_products (
    sold_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);