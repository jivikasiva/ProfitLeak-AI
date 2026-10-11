import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. LOAD DATA
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
returns = pd.read_csv(DATA_DIR / "returns.csv")
marketing = pd.read_csv(DATA_DIR / "marketing_campaigns.csv")

orders["order_date"] = pd.to_datetime(orders["order_date"])
customers["signup_date"] = pd.to_datetime(customers["signup_date"])
returns["return_date"] = pd.to_datetime(returns["return_date"])
marketing["start_date"] = pd.to_datetime(marketing["start_date"])
marketing["end_date"] = pd.to_datetime(marketing["end_date"])

# 2. CREATE ANALYTICAL COLUMNS

orders["gross_revenue"] = (orders["quantity"] * orders["unit_price"])
orders["discount_value"] = (orders["gross_revenue"] * orders["discount_pct"] / 100)
orders["net_sales"] = (orders["gross_revenue"] - orders["discount_value"])
orders["shipping_ratio"] = (orders["shipping_cost"] / orders["gross_revenue"])
orders["month"] = orders["order_date"].dt.to_period("M")

# 3. MERGE ORDERS WITH PRODUCTS
order_analysis = orders.merge(
    products[["product_id","category","subcategory","supplier_id","unit_cost"]],
    on="product_id",
    how="left"
)

order_analysis["gross_profit"] = (
    order_analysis["quantity"] *
    (
        order_analysis["unit_price"] *
        (1 - order_analysis["discount_pct"] / 100)
        - order_analysis["unit_cost"]
    )
)

order_analysis["profit_margin_pct"] = (
    order_analysis["gross_profit"] /
    order_analysis["gross_revenue"] * 100
)


# ============================================================
# 4. DATASET OVERVIEW
# ============================================================

print("\n" + "=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)

for name, df in {
    "Customers": customers,
    "Products": products,
    "Suppliers": suppliers,
    "Orders": orders,
    "Returns": returns,
    "Marketing Campaigns": marketing
}.items():
    print(f"{name}: {df.shape}")


# 5. BASIC BUSINESS KPIs
print("\n\n***BUSINESS KPIs***")
print(f"Total Orders: {len(orders):,}")
print(f"Total Customers: {orders['customer_id'].nunique():,}")
print(f"Total Products: {orders['product_id'].nunique():,}")
print(f"Gross Revenue: ₹{orders['gross_revenue'].sum():,.2f}")
print(f"Net Sales: ₹{orders['net_sales'].sum():,.2f}")
print(f"Discount Value: ₹{orders['discount_value'].sum():,.2f}")
print(f"Average Order Value: ₹{orders['net_sales'].mean():,.2f}")

# 6. MONTHLY SALES TREND

monthly_sales = (orders.groupby("month").agg(
        gross_revenue=("gross_revenue", "sum"),
        net_sales=("net_sales", "sum")).reset_index())
monthly_sales["month"] = (monthly_sales["month"].astype(str))
monthly_sales["mom_growth_pct"] = (monthly_sales["net_sales"] .pct_change() * 100)

print("\n\n***MONTHLY SALES***")
print(monthly_sales.to_string(index=False))
monthly_sales.to_csv(OUTPUT_DIR / "monthly_sales.csv",index=False)

# 7. CATEGORY PROFITABILITY
category_analysis = (order_analysis.groupby("category").agg(
        orders=("order_id", "nunique"), revenue=("gross_revenue", "sum"),
        net_sales=("net_sales", "sum"), gross_profit=("gross_profit", "sum")
    ).reset_index())

category_analysis["profit_margin_pct"] = (
    category_analysis["gross_profit"] / category_analysis["revenue"] * 100)
category_analysis = category_analysis.sort_values("gross_profit", ascending=False)

print("\n\n***CATEGORY PROFITABILITY***")
print(category_analysis.to_string(index=False))
category_analysis.to_csv(OUTPUT_DIR / "category_profitability.csv",index=False)

# 8. RETURN ANALYSIS
return_analysis = returns.merge(
    orders[["order_id","product_id","customer_id","region"]],
    on="order_id",how="left")
return_analysis = return_analysis.merge(
    products[["product_id","category"]],
    on="product_id",how="left")
return_category = ( return_analysis.groupby("category").agg(
        returned_orders=("order_id", "nunique"),
        refund_amount=("refund_amount", "sum"),
        return_shipping=("return_shipping_cost", "sum")
    ).reset_index())
return_category["total_return_leakage"] = (
    return_category["refund_amount"] +
    return_category["return_shipping"]
)

print("\n\n***RETURN LEAKAGE BY CATEGORY***")
print(return_category.sort_values("total_return_leakage", ascending=False).to_string(index=False))
return_category.to_csv(OUTPUT_DIR / "return_analysis.csv",index=False)

# 9. SHIPPING ANALYSIS
shipping = (orders.groupby("region").agg(
        orders=("order_id", "count"),
        avg_shipping=("shipping_cost", "mean"),
        total_shipping=("shipping_cost", "sum")
    ).reset_index())
shipping["high_shipping_cost"] = (orders.assign(
        high_shipping=lambda x:x["shipping_cost"] > x["gross_revenue"] * 0.10)
    .groupby("region")["shipping_cost"]
    .apply(lambda x: x[
            orders.loc[x.index, "shipping_cost"] >
            orders.loc[x.index, "gross_revenue"] * 0.10
        ].sum()).values)

print("\n\n***SHIPPING ANALYSIS***")
print(shipping.to_string(index=False))
shipping.to_csv(OUTPUT_DIR / "shipping_analysis.csv", index=False)

# 10. DISCOUNT ANALYSIS
discount_analysis = (orders.groupby(pd.cut(
            orders["discount_pct"],bins=[-1, 0, 10, 20, 30, 100],
            labels=["0%","1-10%","11-20%","21-30%","31%+"]
        )).agg(orders=("order_id", "count"),gross_revenue=("gross_revenue", "sum"),
            net_sales=("net_sales", "sum"),avg_discount=("discount_pct", "mean"))
    .reset_index())

print("\n\n***DISCOUNT ANALYSIS***")
print(discount_analysis.to_string(index=False))
discount_analysis.to_csv(OUTPUT_DIR / "discount_analysis.csv",index=False)

# 11. PROFIT DISTRIBUTION
print("\n\n***PROFIT DISTRIBUTION***")
print(order_analysis["gross_profit"].describe())

# 12. LOSS-MAKING ORDERS
loss_orders = order_analysis[order_analysis["gross_profit"] < 0]
print("\n\n***LOSS-MAKING ORDERS***")
print(f"Loss-making orders:{len(loss_orders):,}")
print(f"Negative margin value: ₹{abs(loss_orders['gross_profit'].sum()):,.2f}")

# 13. CORRELATION ANALYSIS
correlation_columns = [ "quantity", "unit_price","discount_pct","shipping_cost",
    "delivery_days","gross_revenue","net_sales","gross_profit"]
correlation = order_analysis[correlation_columns].corr()
print("\n\n***CORRELATION MATRIX***")
print(correlation.round(2))
correlation.to_csv( OUTPUT_DIR / "correlation_matrix.csv")

# 14. OUTLIER DETECTION
q1 = orders["gross_revenue"].quantile(0.25)
q3 = orders["gross_revenue"].quantile(0.75)
iqr = q3 - q1
upper_limit = q3 + 1.5 * iqr
revenue_outliers = orders[orders["gross_revenue"] > upper_limit]

print("\n\n***REVENUE OUTLIERS***")
print(f"Upper outlier threshold: ₹{upper_limit:,.2f}")
print(f"Revenue outliers: {len(revenue_outliers):,}")

# 15. SAVE MASTER ANALYTICAL DATASET

order_analysis.to_csv(OUTPUT_DIR / "order_analysis.csv",index=False)

print("\n***EDA COMPLETE***")
print(f"Analysis files saved to: {OUTPUT_DIR}")