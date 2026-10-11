
from pathlib import Path
import pandas as pd

RAW_DIR = Path("../data/raw")

def audit_table(file_path, primary_key=None):
    df = pd.read_csv(file_path)
    print(f"TABLE: {file_path.name}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    #missing values
    print("\n** Missing Values **")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("No missing values.")
    else:
        print(missing)

    #duplicate rows
    print("\n** Duplicate Rows **")
    duplicate_rows = df.duplicated().sum()
    print(f"Duplicate rows: {duplicate_rows:,}")

    # Primary key validation
    if primary_key:
        print("\n** Primary Key Validation **")
        duplicate_ids = df[primary_key].duplicated().sum()
        print(f"{primary_key}: {duplicate_ids:,} duplicate values")

    #data types
    print("\n** Data Types **")
    print(df.dtypes)
    return df


# MAIN AUDIT
def main():
    print("\n\n")
    print("***PROFITLeak AI — DATA QUALITY AUDIT***")
    
    # Load and audit tables
    customers = audit_table(RAW_DIR / "customers.csv",primary_key="customer_id")
    products = audit_table(RAW_DIR / "products.csv",primary_key="product_id")
    suppliers = audit_table(RAW_DIR / "suppliers.csv",primary_key="supplier_id")
    orders = audit_table(RAW_DIR / "orders.csv",primary_key="order_id")
    returns = audit_table(RAW_DIR / "returns.csv",primary_key="return_id")
    campaigns = audit_table(RAW_DIR / "marketing_campaigns.csv",primary_key="campaign_id")

    # FOREIGN KEY VALIDATION
    print("\n\n")
    print("FOREIGN KEY / RELATIONSHIP VALIDATION")
    print("=" * 70)

    # Orders → Customers
    invalid_customers = (~orders["customer_id"].isin(customers["customer_id"])).sum()
    print(f"\nOrders → Customers: {invalid_customers:,} invalid")

    # Orders → Products
    invalid_products = (~orders["product_id"].isin(products["product_id"])).sum()
    print(f"\nOrders → Products: {invalid_products:,} invalid")

    # Products → Suppliers
    invalid_suppliers = (~products["supplier_id"].isin(suppliers["supplier_id"])).sum()
    print(f"\nProducts → Suppliers: {invalid_suppliers:,} invalid")

    # Returns → Orders
    invalid_orders = (~returns["order_id"].isin(orders["order_id"])).sum()
    print(f"\nReturns → Orders: {invalid_orders:,} invalid")

    # ORDERS VALIDATION
    print("\n\n**ORDERS VALIDATION**")

    # Quantity
    invalid_quantity = (orders["quantity"] <= 0).sum()
    print(f"\nInvalid quantity: {invalid_quantity:,}")

    # Unit price
    invalid_price = (orders["unit_price"] <= 0).sum()
    print(f"Invalid unit price: {invalid_price:,}")

    # Discount
    valid_discount = orders["discount_pct"].dropna()
    invalid_discount = ((valid_discount < 0) | (valid_discount > 0.45)).sum()
    print(f"Invalid discount: {invalid_discount:,}")

    # Shipping cost
    valid_shipping = orders["shipping_cost"].dropna()
    invalid_shipping = (valid_shipping < 0).sum()
    print(f"Invalid shipping cost: {invalid_shipping:,}")

    # Delivery days
    invalid_delivery = (orders["delivery_days"] <= 0).sum() 
    print(f"Invalid delivery days: {invalid_delivery:,}")

    # PRODUCTS VALIDATION
    print("\n\n**PRODUCTS VALIDATION**")
    invalid_cost = (products["unit_cost"] <= 0).sum()
    print(f"\nInvalid unit cost:{invalid_cost:,}")

    price_below_cost = (products["unit_price"]<= products["unit_cost"]).sum()
    print(f"Selling price <= unit cost: {price_below_cost:,}")

    # SUPPLIER VALIDATION
    print("\n\n**SUPPLIER VALIDATION**")
    invalid_quality = ((suppliers["quality_score"] < 0)|(suppliers["quality_score"] > 100)).sum()
    print( f"\nQuality score outside 0–100:{invalid_quality:,}")

    # RETURNS VALIDATION
    print("\n\n**RETURNS VALIDATION**")
    negative_refunds = (returns["refund_amount"] < 0).sum()
    print(f"\nNegative refund amount:{negative_refunds:,}")

    negative_shipping = (returns["return_shipping_cost"] < 0).sum()
    print(f"Negative return shipping cost: {negative_shipping:,}")

    # FINAL SUMMARY
    print("\n\n**AUDIT SUMMARY**")

    print(f"""
        Tables audited:
            6
        Orders:
            {len(orders):,}
        Duplicate order rows:
            {orders.duplicated().sum():,}
        Duplicate order IDs:
            {orders["order_id"].duplicated().sum():,}
        Missing discount values:
            {orders["discount_pct"].isna().sum():,}
        Missing shipping values:
            {orders["shipping_cost"].isna().sum():,}
        Broken customer relationships:  
            {invalid_customers:,}
        Broken product relationships:
            {invalid_products:,}
        Broken supplier relationships:
            {invalid_suppliers:,}
        Broken return relationships:
            {invalid_orders:,}
        """)

    
    print("\n**AUDIT COMPLETE**")
    
if __name__ == "__main__":
    main()
