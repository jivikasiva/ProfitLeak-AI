-- ============================================================
-- PROFITLEAK AI
-- 01 - BASIC BUSINESS ANALYSIS
-- ============================================================


-- 1. Total Orders
SELECT
    COUNT(*) AS total_orders
FROM orders;


-- 2. Total Customers
SELECT
    COUNT(*) AS total_customers
FROM customers;


-- 3. Total Products
SELECT
    COUNT(*) AS total_products
FROM products;


-- 4. Total Revenue
SELECT
    ROUND(SUM(quantity * unit_price), 2) AS total_revenue
FROM orders;


-- 5. Revenue After Discount
SELECT
    ROUND(
        SUM(
            quantity * unit_price
            * (1 - discount_pct / 100)
        ),
        2
    ) AS net_sales
FROM orders;


-- 6. Revenue by Region
SELECT
    region,
    COUNT(*) AS total_orders,
    ROUND(
        SUM(quantity * unit_price),
        2
    ) AS revenue
FROM orders
GROUP BY region
ORDER BY revenue DESC;


-- 7. Revenue by Sales Channel
SELECT
    sales_channel,
    COUNT(*) AS total_orders,
    ROUND(
        SUM(quantity * unit_price),
        2
    ) AS revenue
FROM orders
GROUP BY sales_channel
ORDER BY revenue DESC;


-- 8. Revenue by Product Category
SELECT
    p.category,
    COUNT(o.order_id) AS total_orders,
    ROUND(
        SUM(o.quantity * o.unit_price),
        2
    ) AS revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;


-- 9. Monthly Revenue Trend
SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    ROUND(
        SUM(quantity * unit_price),
        2
    ) AS revenue
FROM orders
GROUP BY month
ORDER BY month;


-- 10. Order Status Distribution
SELECT
    order_status,
    COUNT(*) AS order_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;