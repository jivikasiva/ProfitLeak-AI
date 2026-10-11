-- ============================================================
-- ProfitLeak AI - Step 13
-- Intermediate Profitability Analysis
-- ============================================================

-- 1. Monthly Revenue and Net Sales
SELECT
    DATE_TRUNC('month', order_date)::DATE AS month,
    ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
    ROUND(
        SUM(quantity * unit_price * (1 - discount_pct / 100)),
        2
    ) AS net_sales
FROM orders
GROUP BY 1
ORDER BY 1;


-- 2. Category Revenue and Profitability
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue,
    ROUND(
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        ),
        2
    ) AS gross_profit,
    ROUND(
        100.0 *
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        )
        / NULLIF(SUM(o.quantity * o.unit_price), 0),
        2
    ) AS profit_margin_pct
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY gross_profit DESC;


-- 3. Customer Segment Performance
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(o.order_id) AS orders,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue,
    ROUND(
        SUM(o.quantity * o.unit_price * (1 - o.discount_pct / 100)),
        2
    ) AS net_sales,
    ROUND(
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        ),
        2
    ) AS gross_profit
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_segment
ORDER BY net_sales DESC;


-- 4. Return Rate by Category
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT r.order_id) AS returned_orders,
    ROUND(
        100.0 * COUNT(DISTINCT r.order_id)
        / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS return_rate_pct
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
LEFT JOIN returns r
    ON o.order_id = r.order_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;


-- 5. Discount Effectiveness
-- 5. Discount Effectiveness
SELECT
    CASE
        WHEN discount_pct = 0 THEN '0%'
        WHEN discount_pct <= 10 THEN '1-10%'
        WHEN discount_pct <= 20 THEN '11-20%'
        WHEN discount_pct <= 30 THEN '21-30%'
        ELSE '31%+'
    END AS discount_band,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
    ROUND(
        SUM(quantity * unit_price * (1 - discount_pct / 100)),
        2
    ) AS net_sales,
    ROUND(AVG(discount_pct), 2) AS avg_discount_pct
FROM orders
GROUP BY 1
ORDER BY
    MIN(
        CASE
            WHEN discount_pct = 0 THEN 1
            WHEN discount_pct <= 10 THEN 2
            WHEN discount_pct <= 20 THEN 3
            WHEN discount_pct <= 30 THEN 4
            ELSE 5
        END
    );

-- 6. Regional Profitability
SELECT
    o.region,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue,
    ROUND(
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        ),
        2
    ) AS gross_profit,
    ROUND(
        100.0 *
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        )
        / NULLIF(SUM(o.quantity * o.unit_price), 0),
        2
    ) AS profit_margin_pct
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY o.region
ORDER BY gross_profit DESC;


-- 7. Top 20 Products by Gross Profit
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(o.quantity) AS units_sold,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue,
    ROUND(
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        ),
        2
    ) AS gross_profit
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category
ORDER BY gross_profit DESC
LIMIT 20;