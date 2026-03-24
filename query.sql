-- Display Like Sold Item Sheet
SELECT 
    o.order_id,
    c.name AS customer_name,
    p.description AS product_name,
    sp.product_id,
    o.date_sold,
    o.customer_id
FROM sold_products sp
INNER JOIN orders o 
    ON sp.order_id = o.order_id
INNER JOIN customers c 
    ON o.customer_id = c.customer_id
INNER JOIN products p 
    ON sp.product_id = p.product_id;
	
-- Get Stock Query
SELECT 
    *,
    CASE 
        WHEN quantity = 0 THEN 1
        ELSE 0
    END AS sold
FROM products;

-- Display Sold Items with number of products purchased per order
-- Get a summary of orders with optional filters
SELECT
    o.order_id,
    c.name AS customer_name,
    o.date_sold,
    o.total_amount,
    COALESCE(SUM(sp.quantity), 0) AS items_purchased
FROM orders o
INNER JOIN customers c
    ON o.customer_id = c.customer_id
LEFT JOIN sold_products sp
    ON o.order_id = sp.order_id
WHERE
    (:order_id IS NULL OR o.order_id = :order_id)
    AND (:customer_id IS NULL OR o.customer_id = :customer_id)
    AND (:date_from IS NULL OR o.date_sold >= :date_from)
    AND (:date_to IS NULL OR o.date_sold <= :date_to)
GROUP BY
    o.order_id,
    c.name,
    o.date_sold,
    o.total_amount
HAVING
    (:min_items IS NULL OR COALESCE(SUM(sp.quantity), 0) >= :min_items)
    AND (:min_price IS NULL OR o.total_amount >= :min_price)
ORDER BY
    o.date_sold DESC, o.order_id;

-- Get a list of products by order id
SELECT 
    p.product_id,
    p.sku_no,
    p.im_sku,
    p.description,
	sp.quantity,
    p.selling_price,
    p.purchase_price,
    p.date_purchased,
    p."name/address_seller" 
FROM sold_products sp
INNER JOIN products p
    ON sp.product_id = p.product_id
WHERE order_id = 3;

-- Get List of names in sales order 
SELECT 
	c.name,
	o.date_sold
FROM orders o
INNER JOIN customers c
	ON o.customer_id = c.customer_id;