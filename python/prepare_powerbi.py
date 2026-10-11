import pandas as pd
from pathlib import Path

# Power BI Data Preparation

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

print("\n***PROFITLEAK AI — POWER BI DATA PREPARATION***")

# 1. LOAD DATA

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
returns = pd.read_csv(DATA_DIR / "returns.csv")

# 2. PREPARE ORDERS TABLE

orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["gross_revenue"] = (orders["quantity"] * orders["unit_price"])
orders["discount_value"] = (orders["gross_revenue"] * orders["discount_pct"] / 100)
orders["net_sales"] = (orders["gross_revenue"] - orders["discount_value"])
orders["shipping_ratio"] = (orders["shipping_cost"] / orders["gross_revenue"])
orders["high_shipping_cost"] = (orders["shipping_ratio"] > 0.10 )
orders = orders.merge(products[["product_id","category","subcategory","supplier_id","unit_cost"]
    ],on="product_id", how="left")
orders["gross_profit"] = ( orders["quantity"] * (
        orders["unit_price"] * (1 - orders["discount_pct"] / 100) - orders["unit_cost"] ))
orders["profit_margin_pct"] = ( orders["gross_profit"] / orders["gross_revenue"] * 100)
orders["year"] = orders["order_date"].dt.year
orders["month_number"] = orders["order_date"].dt.month
orders["month"] = orders["order_date"].dt.strftime("%Y-%m")

# 3. RETURN FLAG

returned_order_ids = set(returns["order_id"])
orders["was_returned"] = (orders["order_id"].isin(returned_order_ids))

# 4. PREPARE RETURNS TABLE

returns["return_date"] = pd.to_datetime(returns["return_date"])
returns["total_return_cost"] = (returns["refund_amount"] + returns["return_shipping_cost"])
returns = returns.merge(orders[["order_id","product_id","customer_id","region"]],
    on="order_id",how="left")

returns = returns.merge(products[["product_id","product_name","category","subcategory","supplier_id"]],
    on="product_id",how="left")

# 5. PREPARE CUSTOMERS TABLE

customer_metrics = (orders.groupby("customer_id").agg(
        order_count=("order_id", "count"),net_sales=("net_sales", "sum"),
        gross_profit=("gross_profit", "sum"),returned_orders=("was_returned", "sum")
    ).reset_index())

customer_metrics["return_rate_pct"] = (customer_metrics["returned_orders"] / 
                                       customer_metrics["order_count"] * 100)
customers = customers.merge(customer_metrics,on="customer_id", how="left")

customers[["order_count","net_sales","gross_profit", "returned_orders","return_rate_pct"]
          ]= customers[["order_count", "net_sales", "gross_profit",
        "returned_orders","return_rate_pct"]].fillna(0)

# 6. PREPARE BUSINESS FINDINGS
findings = pd.read_csv(ANALYSIS_DIR / "business_findings.csv")

# 7. SAVE POWER BI TABLES
orders_output = ANALYSIS_DIR / "powerbi_orders.csv"
returns_output = ANALYSIS_DIR / "powerbi_returns.csv"
customers_output = ANALYSIS_DIR / "powerbi_customers.csv"
products_output = ANALYSIS_DIR / "powerbi_products.csv"
findings_output = ANALYSIS_DIR / "powerbi_findings.csv"
orders.to_csv(orders_output,index=False)
returns.to_csv(returns_output,index=False)
customers.to_csv(customers_output,index=False)
products.to_csv(DATA_DIR / "products.csv",index=False)
findings.to_csv(findings_output,index=False)

# 8. VALIDATION

print("\nPOWER BI TABLES CREATED")
print("-" * 65)
print(f"Orders:    {len(orders):,} rows | {len(orders.columns)} columns")
print(f"Returns:   {len(returns):,} rows | {len(returns.columns)} columns")
print(f"Customers: {len(customers):,} rows | {len(customers.columns)} columns")
print(f"Products:  {len(products):,} rows | {len(products.columns)} columns")
print(f"Findings:  {len(findings):,} rows | {len(findings.columns)} columns")

print("\nKEY VALIDATION")
print("-" * 65)

print(f"Gross Revenue: ₹{orders['gross_revenue'].sum():,.2f}")
print(f"Net Sales: ₹{orders['net_sales'].sum():,.2f}")
print(f"Gross Profit: ₹{orders['gross_profit'].sum():,.2f}")
print(f"Returned Orders: {orders['was_returned'].sum():,.0f}")
print(f"High Shipping Cost Orders: {orders['high_shipping_cost'].sum():,.0f}")

print("\n" + "=" * 65)
print("POWER BI PREPARATION COMPLETE")
print("=" * 65)