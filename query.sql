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
	
SELECT * FROM orders;