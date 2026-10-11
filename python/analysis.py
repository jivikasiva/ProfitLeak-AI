import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. LOAD DATA

orders = pd.read_csv(DATA_DIR / "orders.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
customers = pd.read_csv(DATA_DIR / "customers.csv")
returns = pd.read_csv(DATA_DIR / "returns.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")

orders["order_date"] = pd.to_datetime(orders["order_date"])
returns["return_date"] = pd.to_datetime(returns["return_date"])

# 2. CREATE BUSINESS METRICS

orders["gross_revenue"] = (orders["quantity"] * orders["unit_price"])
orders["discount_value"] = (orders["gross_revenue"] * orders["discount_pct"] / 100)
orders["net_sales"] = ( orders["gross_revenue"] - orders["discount_value"])
orders["shipping_ratio"] = ( orders["shipping_cost"] / orders["gross_revenue"])

# Merge product information
df = orders.merge(products[[
            "product_id","product_name","category","subcategory",
            "supplier_id","unit_cost"]],on="product_id", how="left")

df["gross_profit"] = (df["quantity"] *(df["unit_price"] *
        (1 - df["discount_pct"] / 100) - df["unit_cost"]))

df["profit_margin_pct"] = (df["gross_profit"] / df["gross_revenue"] * 100)

# 3. DISCOUNT EFFECTIVENESS
print("\n\n***1. DISCOUNT EFFECTIVENESS***")

df["discount_band"] = pd.cut(df["discount_pct"],
    bins=[-1, 0, 2, 5, 10, 100],
    labels=["0%","1-2%","3-5%", "6-10%","10%+"])

discount_effectiveness = (df.groupby("discount_band", observed=False)
    .agg(orders=("order_id", "count"),avg_order_value=("net_sales", "mean"),
        revenue=("gross_revenue", "sum"),net_sales=("net_sales", "sum"),
        profit=("gross_profit", "sum"),avg_profit=("gross_profit", "mean")
    ).reset_index())

discount_effectiveness["margin_pct"] = (
    discount_effectiveness["profit"] /
    discount_effectiveness["revenue"] * 100
)

print(discount_effectiveness.to_string(index=False))

discount_effectiveness.to_csv(OUTPUT_DIR / "advanced_discount_effectiveness.csv",index=False)

# 4. RETURN RATE BY PRODUCT

print("\n\n***2. PRODUCTS WITH HIGHEST RETURN RATE***")

returned_product = (returns.merge(df[["order_id","product_id","customer_id","quantity"]],
        on="order_id",how="left"))

product_orders = (df.groupby("product_id")
    .agg(total_orders=("order_id", "nunique"),total_units=("quantity", "sum"))
    .reset_index())

product_returns = (returned_product.groupby("product_id")
    .agg(returned_orders=("order_id", "nunique"),
        refund_amount=("refund_amount", "sum"),
        return_shipping=("return_shipping_cost", "sum")
    ).reset_index())

product_return_analysis = product_orders.merge(product_returns,
    on="product_id",how="left")

product_return_analysis[["returned_orders", "refund_amount", "return_shipping"]
    ] = product_return_analysis[["returned_orders", "refund_amount", "return_shipping"]].fillna(0)

product_return_analysis["return_rate_pct"] = (
    product_return_analysis["returned_orders"] /
    product_return_analysis["total_orders"] * 100)

product_return_analysis["return_cost"] = (
    product_return_analysis["refund_amount"] +
    product_return_analysis["return_shipping"])

product_return_analysis = product_return_analysis.merge(
    products[["product_id","product_name","category","supplier_id"]],
    on="product_id",how="left")

high_return_products = (product_return_analysis[product_return_analysis["total_orders"] >= 30]
    .sort_values(["return_rate_pct", "return_cost"],ascending=False).head(20))

print(high_return_products.to_string(index=False))

high_return_products.to_csv(OUTPUT_DIR / "high_return_products.csv",index=False)

# 5. RETURN REASONS

print("\n\n***3. RETURN REASONS***")

return_reasons = (returns.groupby("return_reason").agg(
        returns=("return_id", "count"),refund=("refund_amount", "sum"),
        shipping_cost=("return_shipping_cost", "sum")).reset_index())

return_reasons["total_cost"] = (return_reasons["refund"] + return_reasons["shipping_cost"])
return_reasons["return_share_pct"] = (return_reasons["returns"] /
    return_reasons["returns"].sum() * 100)

return_reasons = return_reasons.sort_values("total_cost",ascending=False)
print(return_reasons.to_string(index=False))
return_reasons.to_csv(OUTPUT_DIR / "return_reasons.csv",index=False)

# 6. DELIVERY DAYS VS RETURN BEHAVIOR

print("\n\n***4. DELIVERY TIME VS RETURNS***")

return_orders = returns["order_id"].unique()
df["was_returned"] = (df["order_id"].isin(return_orders))

delivery_analysis = (df.groupby("delivery_days").agg(
        orders=("order_id", "count"),returned_orders=("was_returned", "sum")
    ).reset_index())

delivery_analysis["return_rate_pct"] = (
    delivery_analysis["returned_orders"] /
    delivery_analysis["orders"] * 100)

print(delivery_analysis.to_string(index=False))
delivery_analysis.to_csv(OUTPUT_DIR / "delivery_vs_returns.csv",index=False)

# 7. REGIONAL OPERATIONAL ANALYSIS

print("\n***5. REGIONAL OPERATIONAL PERFORMANCE***")

regional = (
    df.groupby("region")
    .agg(
        orders=("order_id", "count"),
        revenue=("gross_revenue", "sum"),
        profit=("gross_profit", "sum"),
        avg_shipping=("shipping_cost", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
        returned_orders=("was_returned", "sum")
    )
    .reset_index()
)

regional["return_rate_pct"] = (
    regional["returned_orders"] /
    regional["orders"] * 100
)

regional["profit_margin_pct"] = (
    regional["profit"] /
    regional["revenue"] * 100
)

print(regional.to_string(index=False))

regional.to_csv(
    OUTPUT_DIR / "regional_operational_analysis.csv",
    index=False
)


# ============================================================
# 8. SUPPLIER PERFORMANCE
# ============================================================

print("\n" + "=" * 65)
print("6. SUPPLIER PERFORMANCE")
print("=" * 65)

supplier_analysis = (
    df.groupby("supplier_id")
    .agg(
        orders=("order_id", "count"),
        revenue=("gross_revenue", "sum"),
        profit=("gross_profit", "sum"),
        avg_delivery_days=("delivery_days", "mean")
    )
    .reset_index()
)

supplier_analysis["margin_pct"] = (
    supplier_analysis["profit"] /
    supplier_analysis["revenue"] * 100
)

supplier_analysis = supplier_analysis.merge(
    suppliers[
        [
            "supplier_id",
            "supplier_name",
            "region",
            "quality_score",
            "avg_lead_days"
        ]
    ],
    on="supplier_id",
    how="left"
)

supplier_analysis["delivery_gap"] = (
    supplier_analysis["avg_delivery_days"] -
    supplier_analysis["avg_lead_days"]
)

supplier_analysis = supplier_analysis.sort_values(
    "delivery_gap",
    ascending=False
)

print(
    supplier_analysis.head(20).to_string(index=False)
)

supplier_analysis.to_csv(
    OUTPUT_DIR / "supplier_performance.csv",
    index=False
)


# ============================================================
# 9. CUSTOMER RETURN BEHAVIOR
# ============================================================

print("\n" + "=" * 65)
print("7. CUSTOMER RETURN BEHAVIOR")
print("=" * 65)

customer_orders = (
    df.groupby("customer_id")
    .agg(
        orders=("order_id", "count"),
        revenue=("net_sales", "sum"),
        profit=("gross_profit", "sum")
    )
    .reset_index()
)

customer_returns = (
    returned_product.groupby("customer_id")
    .agg(
        returned_orders=("order_id", "nunique"),
        refund=("refund_amount", "sum"),
        return_shipping=("return_shipping_cost", "sum")
    )


    .reset_index()
)

customer_analysis = customer_orders.merge(
    customer_returns,
    on="customer_id",
    how="left"
)

customer_analysis[
    ["returned_orders", "refund", "return_shipping"]
] = customer_analysis[
    ["returned_orders", "refund", "return_shipping"]
].fillna(0)

customer_analysis["return_rate_pct"] = (
    customer_analysis["returned_orders"] /
    customer_analysis["orders"] * 100
)

customer_analysis["return_cost"] = (
    customer_analysis["refund"] +
    customer_analysis["return_shipping"]
)

high_risk_customers = (
    customer_analysis[
        (customer_analysis["orders"] >= 5) &
        (customer_analysis["return_rate_pct"] >= 30)
    ]
    .sort_values(
        "return_cost",
        ascending=False
    )
    .head(20)
)

print(high_risk_customers.to_string(index=False))

high_risk_customers.to_csv(
    OUTPUT_DIR / "high_risk_customers.csv",
    index=False
)


# ============================================================
# 10. CORRELATION: DELIVERY / SHIPPING / RETURNS / PROFIT
# ============================================================

print("\n" + "=" * 65)
print("8. OPERATIONAL CORRELATIONS")
print("=" * 65)

correlation_columns = [
    "delivery_days",
    "shipping_cost",
    "shipping_ratio",
    "discount_pct",
    "quantity",
    "gross_revenue",
    "gross_profit",
    "was_returned"
]

operational_correlation = df[
    correlation_columns
].corr()

print(
    operational_correlation.round(3)
)

operational_correlation.to_csv(
    OUTPUT_DIR / "operational_correlations.csv"
)


# ============================================================
# 11. PARETO ANALYSIS — RETURN COST
# ============================================================

print("\n" + "=" * 65)
print("9. RETURN COST CONCENTRATION")
print("=" * 65)

product_return_pareto = (
    product_return_analysis
    .sort_values("return_cost", ascending=False)
    .copy()
)

product_return_pareto["cumulative_cost_pct"] = (
    product_return_pareto["return_cost"].cumsum() /
    product_return_pareto["return_cost"].sum() * 100
)

products_for_80_pct = (
    product_return_pareto[
        product_return_pareto["cumulative_cost_pct"] <= 80
    ]
)

print(
    f"Products contributing up to 80% of return cost: "
    f"{len(products_for_80_pct):,}"
)

print(
    f"Total products: "
    f"{len(product_return_pareto):,}"
)

product_return_pareto.to_csv(
    OUTPUT_DIR / "return_cost_pareto.csv",
    index=False
)


# ============================================================
# 12. FINAL AUTOMATED FINDINGS
# ============================================================

print("\n" + "=" * 65)
print("10. KEY DATA-DRIVEN FINDINGS")
print("=" * 65)

highest_shipping_region = regional.loc[
    regional["avg_shipping"].idxmax()
]

highest_return_region = regional.loc[
    regional["return_rate_pct"].idxmax()
]

highest_margin_category = (
    df.groupby("category")["gross_profit"].sum() /
    df.groupby("category")["gross_revenue"].sum() * 100
).idxmax()

highest_return_reason = return_reasons.iloc[0]

print(
    f"Highest average shipping region: "
    f"{highest_shipping_region['region']} "
    f"(₹{highest_shipping_region['avg_shipping']:.2f})"
)

print(
    f"Highest return-rate region: "
    f"{highest_return_region['region']} "
    f"({highest_return_region['return_rate_pct']:.2f}%)"
)

print(
    f"Highest-margin category: "
    f"{highest_margin_category}"
)

print(
    f"Highest return-cost reason: "
    f"{highest_return_reason['return_reason']} "
    f"(₹{highest_return_reason['total_cost']:,.2f})"
)

print("\n" + "=" * 65)
print("ADVANCED ANALYSIS COMPLETE")
print("=" * 65)

print(
    f"Results saved to: {OUTPUT_DIR}"
)