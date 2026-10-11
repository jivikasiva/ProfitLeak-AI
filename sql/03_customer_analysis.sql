-- ============================================================
-- ProfitLeak AI - Step 14
-- Advanced Customer & Business Analysis
-- ============================================================


-- 1. Customer Lifetime Value
WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.customer_segment,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(o.quantity * o.unit_price * (1 - o.discount_pct / 100)) AS net_sales,
        SUM(
            o.quantity *
            (o.unit_price * (1 - o.discount_pct / 100) - p.unit_cost)
        ) AS gross_profit
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    JOIN products p
        ON o.product_id = p.product_id
    GROUP BY
        c.customer_id,
        c.customer_segment
)
SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(AVG(total_orders), 2) AS avg_orders,
    ROUND(AVG(net_sales), 2) AS avg_customer_value,
    ROUND(AVG(gross_profit), 2) AS avg_customer_profit,
    ROUND(MAX(net_sales), 2) AS highest_customer_value
FROM customer_metrics
GROUP BY customer_segment
ORDER BY avg_customer_value DESC;


-- 2. Top 20 Customers by Net Sales
WITH customer_sales AS (
    SELECT
        c.customer_id,
        c.customer_segment,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(
            o.quantity *
            o.unit_price *
            (1 - o.discount_pct / 100)
        ) AS net_sales
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY
        c.customer_id,
        c.customer_segment
)
SELECT
    customer_id,
    customer_segment,
    total_orders,
    ROUND(net_sales, 2) AS net_sales,
    RANK() OVER (
        ORDER BY net_sales DESC
    ) AS sales_rank
FROM customer_sales
ORDER BY net_sales DESC
LIMIT 20;


-- 3. Customer Revenue Concentration / Pareto Analysis
WITH customer_sales AS (
    SELECT
        customer_id,
        SUM(
            quantity *
            unit_price *
            (1 - discount_pct / 100)
        ) AS net_sales
    FROM orders
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        net_sales,
        SUM(net_sales) OVER (
            ORDER BY net_sales DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_sales,
        SUM(net_sales) OVER () AS total_sales
    FROM customer_sales
)
SELECT
    customer_id,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(
        100.0 * cumulative_sales / total_sales,
        2
    ) AS cumulative_sales_pct
FROM ranked_customers
ORDER BY net_sales DESC
LIMIT 50;


-- 4. Month-over-Month Revenue Growth
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS month,
        SUM(
            quantity *
            unit_price *
            (1 - discount_pct / 100)
        ) AS net_sales
    FROM orders
    GROUP BY 1
),
growth AS (
    SELECT
        month,
        net_sales,
        LAG(net_sales) OVER (
            ORDER BY month
        ) AS previous_month_sales
    FROM monthly_sales
)
SELECT
    month,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(previous_month_sales, 2) AS previous_month_sales,
    ROUND(
        100.0 *
        (net_sales - previous_month_sales)
        / NULLIF(previous_month_sales, 0),
        2
    ) AS mom_growth_pct
FROM growth
ORDER BY month;


-- 5. Return Behavior by Customer Segment
SELECT
    c.customer_segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT r.order_id) AS returned_orders,
    ROUND(
        100.0 *
        COUNT(DISTINCT r.order_id)
        / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS return_rate_pct,
    ROUND(
        COALESCE(SUM(r.refund_amount), 0),
        2
    ) AS refund_amount,
    ROUND(
        COALESCE(SUM(r.return_shipping_cost), 0),
        2
    ) AS return_shipping_cost
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
LEFT JOIN returns r
    ON o.order_id = r.order_id
GROUP BY c.customer_segment
ORDER BY return_rate_pct DESC;


-- 6. Customer Acquisition Channel Performance
SELECT
    c.acquisition_channel,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(
        SUM(
            o.quantity *
            o.unit_price *
            (1 - o.discount_pct / 100)
        ),
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
GROUP BY c.acquisition_channel
ORDER BY net_sales DESC;


-- 7. Customer Recency and Frequency
WITH customer_activity AS (
    SELECT
        c.customer_id,
        c.customer_segment,
        MAX(o.order_date) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS order_frequency,
        SUM(
            o.quantity *
            o.unit_price *
            (1 - o.discount_pct / 100)
        ) AS net_sales
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY
        c.customer_id,
        c.customer_segment
)
SELECT
    customer_segment,
    COUNT(*) AS active_customers,
    ROUND(AVG(order_frequency), 2) AS avg_order_frequency,
    ROUND(AVG(net_sales), 2) AS avg_net_sales,
    MIN(last_order_date) AS earliest_last_order,
    MAX(last_order_date) AS latest_last_order
FROM customer_activity
GROUP BY customer_segment
ORDER BY avg_net_sales DESC;