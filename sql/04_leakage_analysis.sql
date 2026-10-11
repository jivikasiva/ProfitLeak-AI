-- ============================================================
-- ProfitLeak AI - Step 15
-- Profit Leakage Analysis
-- ============================================================


-- 1. DISCOUNT LEAKAGE
-- Revenue given away through discounts

SELECT
    ROUND(
        SUM(
            quantity * unit_price * (discount_pct / 100)
        ),
        2
    ) AS total_discount_value,
    ROUND(
        AVG(discount_pct),
        2
    ) AS avg_discount_pct,
    COUNT(*) FILTER (WHERE discount_pct > 0) AS discounted_orders
FROM orders;


-- 2. RETURN LEAKAGE
-- Refunds + return shipping costs

SELECT
    COUNT(DISTINCT r.order_id) AS returned_orders,
    ROUND(SUM(r.refund_amount), 2) AS total_refunds,
    ROUND(SUM(r.return_shipping_cost), 2) AS return_shipping_cost,
    ROUND(
        SUM(r.refund_amount + r.return_shipping_cost),
        2
    ) AS total_return_leakage
FROM returns r;


-- 3. RETURN LEAKAGE BY CATEGORY

SELECT
    p.category,
    COUNT(DISTINCT r.order_id) AS returned_orders,
    ROUND(SUM(r.refund_amount), 2) AS refunds,
    ROUND(SUM(r.return_shipping_cost), 2) AS return_shipping,
    ROUND(
        SUM(r.refund_amount + r.return_shipping_cost),
        2
    ) AS total_return_leakage
FROM returns r
JOIN orders o
    ON r.order_id = o.order_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY total_return_leakage DESC;


-- 4. SHIPPING LEAKAGE
-- Identify expensive shipping relative to order value

WITH shipping_analysis AS (
    SELECT
        order_id,
        quantity * unit_price AS order_value,
        shipping_cost
    FROM orders
)
SELECT
    COUNT(*) AS total_orders,
    ROUND(AVG(shipping_cost), 2) AS avg_shipping_cost,
    ROUND(SUM(shipping_cost), 2) AS total_shipping_cost,
    ROUND(
        SUM(
            CASE
                WHEN shipping_cost > order_value * 0.10
                THEN shipping_cost
                ELSE 0
            END
        ),
        2
    ) AS high_shipping_cost
FROM shipping_analysis;


-- 5. SHIPPING LEAKAGE BY REGION

SELECT
    region,
    COUNT(*) AS orders,
    ROUND(AVG(shipping_cost), 2) AS avg_shipping_cost,
    ROUND(SUM(shipping_cost), 2) AS total_shipping_cost,
    ROUND(
        SUM(
            CASE
                WHEN shipping_cost > quantity * unit_price * 0.10
                THEN shipping_cost
                ELSE 0
            END
        ),
        2
    ) AS high_shipping_cost
FROM orders
GROUP BY region
ORDER BY high_shipping_cost DESC;


-- 6. MARGIN LEAKAGE
-- Orders where discount significantly reduces margin

WITH margin_analysis AS (
    SELECT
        o.order_id,
        p.category,
        o.quantity,
        o.unit_price,
        p.unit_cost,
        o.discount_pct,
        (
            o.quantity *
            (
                o.unit_price *
                (1 - o.discount_pct / 100)
                - p.unit_cost
            )
        ) AS profit
    FROM orders o
    JOIN products p
        ON o.product_id = p.product_id
)
SELECT
    category,
    COUNT(*) AS orders,
    ROUND(
        AVG(discount_pct),
        2
    ) AS avg_discount_pct,
    ROUND(
        SUM(profit),
        2
    ) AS total_profit,
    COUNT(*) FILTER (
        WHERE profit < 0
    ) AS loss_making_orders,
    ROUND(
        SUM(
            CASE
                WHEN profit < 0 THEN ABS(profit)
                ELSE 0
            END
        ),
        2
    ) AS negative_margin_value
FROM margin_analysis
GROUP BY category
ORDER BY negative_margin_value DESC;


-- 7. CUSTOMER LEAKAGE
-- Customers with high returns and low profitability

WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.customer_segment,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(
            o.quantity *
            o.unit_price *
            (1 - o.discount_pct / 100)
        ) AS net_sales,
        SUM(
            o.quantity *
            (
                o.unit_price *
                (1 - o.discount_pct / 100)
                - p.unit_cost
            )
        ) AS gross_profit,
        COUNT(DISTINCT r.order_id) AS returned_orders,
        COALESCE(
            SUM(r.refund_amount + r.return_shipping_cost),
            0
        ) AS return_cost
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    JOIN products p
        ON o.product_id = p.product_id
    LEFT JOIN returns r
        ON o.order_id = r.order_id
    GROUP BY
        c.customer_id,
        c.customer_segment
)
SELECT
    customer_segment,
    COUNT(*) FILTER (
        WHERE return_cost > gross_profit * 0.20
    ) AS high_return_cost_customers,
    ROUND(
        SUM(return_cost),
        2
    ) AS total_customer_return_cost,
    ROUND(
        SUM(gross_profit),
        2
    ) AS total_gross_profit
FROM customer_metrics
GROUP BY customer_segment
ORDER BY total_customer_return_cost DESC;


-- 8. ACQUISITION LEAKAGE
-- Compare marketing budget with generated customer revenue

WITH channel_revenue AS (
    SELECT
        c.acquisition_channel,
        COUNT(DISTINCT c.customer_id) AS customers,
        SUM(
            o.quantity *
            o.unit_price *
            (1 - o.discount_pct / 100)
        ) AS net_sales
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY c.acquisition_channel
),
campaign_budget AS (
    SELECT
        CASE
            WHEN LOWER(channel) LIKE '%search%'
                THEN 'Paid Search'
            WHEN LOWER(channel) LIKE '%social%'
                THEN 'Social Media'
            WHEN LOWER(channel) LIKE '%email%'
                THEN 'Email'
            WHEN LOWER(channel) LIKE '%affiliate%'
                THEN 'Affiliate'
            ELSE channel
        END AS acquisition_channel,
        SUM(budget) AS total_budget
    FROM marketing_campaigns
    GROUP BY 1
)
SELECT
    cr.acquisition_channel,
    cr.customers,
    ROUND(cr.net_sales, 2) AS net_sales,
    ROUND(COALESCE(cb.total_budget, 0), 2) AS marketing_budget,
    ROUND(
        cr.net_sales /
        NULLIF(cb.total_budget, 0),
        2
    ) AS revenue_per_budget
FROM channel_revenue cr
LEFT JOIN campaign_budget cb
    ON cr.acquisition_channel = cb.acquisition_channel
ORDER BY revenue_per_budget DESC NULLS LAST;


-- 9. OVERALL LEAKAGE SUMMARY

-- 9. OVERALL LEAKAGE SUMMARY

WITH discount_leakage AS (
    SELECT
        SUM(
            o.quantity * o.unit_price * o.discount_pct / 100
        ) AS leakage
    FROM orders o
),
return_leakage AS (
    SELECT
        SUM(r.refund_amount + r.return_shipping_cost) AS leakage
    FROM returns r
),
shipping_leakage AS (
    SELECT
        SUM(
            CASE
                WHEN o.shipping_cost >
                     o.quantity * o.unit_price * 0.10
                THEN o.shipping_cost
                ELSE 0
            END
        ) AS leakage
    FROM orders o
),
margin_leakage AS (
    SELECT
        SUM(
            CASE
                WHEN
                    o.quantity *
                    (
                        o.unit_price *
                        (1 - o.discount_pct / 100)
                        - p.unit_cost
                    ) < 0
                THEN ABS(
                    o.quantity *
                    (
                        o.unit_price *
                        (1 - o.discount_pct / 100)
                        - p.unit_cost
                    )
                )
                ELSE 0
            END
        ) AS leakage
    FROM orders o
    JOIN products p
        ON o.product_id = p.product_id
)

SELECT
    'Discount Leakage' AS leakage_type,
    ROUND(leakage, 2) AS leakage_amount
FROM discount_leakage

UNION ALL

SELECT
    'Return Leakage',
    ROUND(leakage, 2)
FROM return_leakage

UNION ALL

SELECT
    'Shipping Leakage',
    ROUND(leakage, 2)
FROM shipping_leakage

UNION ALL

SELECT
    'Margin Leakage',
    ROUND(leakage, 2)
FROM margin_leakage

ORDER BY leakage_amount DESC;