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
    ON sp.order_id = o.order_id
GROUP BY o.order_id, c.name, o.date_sold, o.total_amount
ORDER BY o.date_sold DESC;

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