import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

print("PROFITLEAK AI - DATA CLEANING")

customers = pd.read_csv(RAW_DIR / "customers.csv")
products = pd.read_csv(RAW_DIR / "products.csv")
suppliers = pd.read_csv(RAW_DIR / "suppliers.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")
returns = pd.read_csv(RAW_DIR / "returns.csv")
marketing = pd.read_csv(RAW_DIR / "marketing_campaigns.csv")
print("\nRaw data loaded successfully.")

# 1. REMOVE DUPLICATE ORDERS
print("\n[1] Removing duplicate orders...")
before = len(orders)
orders = orders.drop_duplicates(subset="order_id", keep="first")
after = len(orders)
print(f"Rows before: {before:,}")
print(f"Rows after : {after:,}")
print(f"Duplicates removed: {before - after:,}")

# 2. HANDLE MISSING DISCOUNT
print("\n[2] Handling missing discount_pct...")
missing_discount = orders["discount_pct"].isna().sum()
orders["discount_pct"] = orders["discount_pct"].fillna(0)
print(f"Missing discount values handled: {missing_discount}")

# 3. HANDLE MISSING SHIPPING COST
print("\n[3] Handling missing shipping_cost...")
missing_shipping = orders["shipping_cost"].isna().sum()
shipping_median = orders["shipping_cost"].median()
orders["shipping_cost"] = orders["shipping_cost"].fillna(shipping_median)
print(f"Missing shipping values handled: {missing_shipping}")
print(f"Median shipping cost used: {shipping_median:.2f}")

# 4. CONVERT DATE COLUMNS
print("\n[4] Converting date columns...")
customers["signup_date"] = pd.to_datetime(customers["signup_date"],errors="coerce")
orders["order_date"] = pd.to_datetime(orders["order_date"],errors="coerce")
returns["return_date"] = pd.to_datetime(returns["return_date"],errors="coerce")
marketing["start_date"] = pd.to_datetime(marketing["start_date"],errors="coerce")   
marketing["end_date"] = pd.to_datetime(marketing["end_date"],errors="coerce")
print("Date conversion completed.")

# 5. VALIDATE CLEANED DATA
print("\n[5] Validating cleaned data...")
print("\nDuplicate orders:")
print(orders["order_id"].duplicated().sum())
print("\nMissing values in orders:")
print(orders.isna().sum())
print("\nInvalid quantities:")
print((orders["quantity"] <= 0).sum())
print("\nInvalid unit prices:")
print((orders["unit_price"] <= 0).sum())
invalid_discounts = ((orders["discount_pct"] < 0) | (orders["discount_pct"] > 100)).sum()
print(f"\nInvalid discounts:{invalid_discounts}")
print("\nInvalid shipping costs:")
print((orders["shipping_cost"] < 0).sum())

# 6. VALIDATE RELATIONSHIPS
print("\n[6] Validating relationships...")
invalid_customer = (~orders["customer_id"].isin(customers["customer_id"])).sum()
invalid_product = (~orders["product_id"].isin(products["product_id"])).sum()
invalid_supplier = (~products["supplier_id"].isin(suppliers["supplier_id"])).sum()
invalid_return_order = (~returns["order_id"].isin(orders["order_id"])).sum()

print(f"Invalid customer references : {invalid_customer}")
print(f"Invalid product references  : {invalid_product}")
print(f"Invalid supplier references : {invalid_supplier}")
print(f"Invalid return references   : {invalid_return_order}")

# 7. SAVE CLEANED DATA
print("\n[7] Saving cleaned datasets...")
customers.to_csv(CLEANED_DIR / "customers.csv",index=False)
products.to_csv(CLEANED_DIR / "products.csv",index=False)
suppliers.to_csv(CLEANED_DIR / "suppliers.csv",index=False)
orders.to_csv(CLEANED_DIR / "orders.csv",index=False)
returns.to_csv(CLEANED_DIR / "returns.csv",index=False)
marketing.to_csv(CLEANED_DIR / "marketing_campaigns.csv",index=False)


print("\n" + "=" * 60)
print("DATA CLEANING COMPLETED")
print(f"\nCustomers : {len(customers):,}")
print(f"Products  : {len(products):,}")
print(f"Suppliers : {len(suppliers):,}")
print(f"Orders    : {len(orders):,}")
print(f"Returns   : {len(returns):,}")
print(f"Marketing : {len(marketing):,}")

print(f"\nCleaned files saved to:")
print(CLEANED_DIR)

print("\nRaw files were NOT modified.")