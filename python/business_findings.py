import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "analysis"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"
findings = []

def add_finding(area,observation,root_cause,
    financial_impact, priority, recommendation ):
    findings.append({
        "area": area,
        "observation": observation,
        "root_cause": root_cause,
        "financial_impact": financial_impact,
        "priority": priority,
        "recommendation": recommendation
    })

discount = pd.read_csv(DATA_DIR / "advanced_discount_effectiveness.csv")
products = pd.read_csv(DATA_DIR / "high_return_products.csv")
return_reasons = pd.read_csv(DATA_DIR / "return_reasons.csv")
regional = pd.read_csv(DATA_DIR / "regional_operational_analysis.csv")
suppliers = pd.read_csv(DATA_DIR / "supplier_performance.csv")
customers = pd.read_csv(DATA_DIR / "high_risk_customers.csv")
pareto = pd.read_csv(DATA_DIR / "return_cost_pareto.csv")

# 1. RETURN QUALITY PROBLEM

quality = return_reasons[ return_reasons["return_reason"] == "Quality Issue"]

if not quality.empty:
    quality_cost = quality.iloc[0]["total_cost"]
    add_finding(
        area="Product Quality",
        observation=("Quality issues are the largest identified ""return-cost category."),
        root_cause=("A significant share of returns is associated ""with product quality problems."),
        financial_impact=(f"₹{quality_cost:,.2f} in refund and return-shipping cost."),
        priority="HIGH",
        recommendation=(
            "Investigate high-return products and suppliers, "
            "strengthen quality checks, and review supplier "
            "performance before increasing product exposure."
        )
    )

# 2. LATE DELIVERY

late = return_reasons[return_reasons["return_reason"] == "Late Delivery"]
if not late.empty:
    late_cost = late.iloc[0]["total_cost"]
    add_finding(
        area="Delivery Operations",
        observation="Late delivery is the second-largest return-cost reason.",
        root_cause=(
            "Delivery-related failures are contributing materially "
            "to customer returns."),
        financial_impact=f"₹{late_cost:,.2f} in return-related cost.",
        priority="HIGH",
        recommendation=(
            "Investigate fulfillment and logistics performance "
            "by region and supplier, and establish delivery "
            "performance monitoring."
        )
    )

# 3. HIGH RETURN PRODUCTS

if not products.empty:
    top_product = products.iloc[0]
    add_finding(
        area="Product Return Risk",
        observation=(
            f"{top_product['product_id']} has a "
            f"{top_product['return_rate_pct']:.2f}% return rate "
            f"among products with sufficient order volume."
        ),
        root_cause=(
            "A small group of products shows substantially "
            "higher return rates than the overall business."
        ),
        financial_impact=(
            f"₹{top_product['return_cost']:,.2f} return cost "
            f"for the highest-return-rate product identified."
        ),
        priority="HIGH",
        recommendation=(
            "Perform product-level root-cause analysis covering "
            "quality, description accuracy, sizing, packaging, "
            "and supplier performance."
        )
    )

# 4. SHIPPING INEFFICIENCY

highest_shipping = regional.loc[regional["avg_shipping"].idxmax()]
add_finding(
    area="Shipping",
    observation=(
        f"{highest_shipping['region']} has the highest average "
        f"shipping cost at ₹{highest_shipping['avg_shipping']:.2f} "
        f"per order."
    ),
    root_cause=(
        "Shipping cost varies materially by region, indicating "
        "an opportunity to investigate logistics efficiency."
    ),
    financial_impact=(
        f"₹{highest_shipping['avg_shipping']:.2f} average "
        f"shipping cost per order in the highest-cost region."
    ),
    priority="HIGH",
    recommendation=(
        "Review carrier, distance, weight, fulfillment-center "
        "and shipping-method patterns in high-cost regions."
    )
)

# 5. CUSTOMER RETURN RISK

if not customers.empty:
    top_customer = customers.iloc[0]
    add_finding(
        area="Customer Leakage",
        observation=(
            f"{top_customer['customer_id']} has a "
            f"{top_customer['return_rate_pct']:.2f}% return rate "
            f"across {int(top_customer['orders'])} orders."
        ),
        root_cause=(
            "Some repeat customers exhibit unusually high "
            "return behavior."
        ),
        financial_impact=(
            f"₹{top_customer['return_cost']:,.2f} return cost "
            f"associated with the highest-cost high-risk customer."
        ),
        priority="MEDIUM",
        recommendation=(
            "Create customer-level return-risk monitoring and "
            "investigate repeated return patterns before applying "
            "retention incentives."
        )
    )

# 6. SUPPLIER DELIVERY GAP

if not suppliers.empty:
    top_supplier = suppliers.iloc[0]
    add_finding(
        area="Supplier Performance",
        observation=(
            f"{top_supplier['supplier_id']} has the largest "
            f"delivery gap among the suppliers identified."
        ),
        root_cause=(
            "Actual average delivery time exceeds the supplier's "
            "average lead-time expectation."
        ),
        financial_impact=(
            f"{top_supplier['delivery_gap']:.2f} days delivery gap."
        ),
        priority="MEDIUM",
        recommendation=(
            "Review supplier SLA adherence, fulfillment delays "
            "and order-routing decisions."
        )
    )

# 7. RETURN COST CONCENTRATION

products_80 = int((pareto["cumulative_cost_pct"] <= 80).sum())
total_products = len(pareto)
add_finding(
    area="Return Cost Concentration",
    observation=(
        f"{products_80:,} of {total_products:,} products "
        "account for the first 80% of cumulative return cost."
    ),
    root_cause=(
        "Return costs are distributed across a broad product "
        "base rather than being concentrated in a very small "
        "number of products."
    ),
    financial_impact=(
        "The majority of return cost requires product-level "
        "monitoring across a substantial portion of the catalog."
    ),
    priority="MEDIUM",
    recommendation=(
        "Use a return-risk score to continuously rank products "
        "and prioritize investigation based on both return rate "
        "and financial impact."
    )
)

# 8. DISCOUNT FINDING

discounted = discount[discount["discount_band"] == "1-2%"]
if not discounted.empty:
    row = discounted.iloc[0]
    add_finding(
        area="Discount Strategy",
        observation=(
            "The dataset shows extremely limited discount variation; "
            "almost all orders fall within the 1-2% discount band."
        ),
        root_cause=(
            "The current dataset does not contain enough discount "
            "variation to establish a strong causal relationship "
            "between discount level and sales performance."
        ),
        financial_impact=(
            f"Observed discount value is approximately "
            f"₹{(row['revenue'] - row['net_sales']):,.2f} "
            "within this analysis."
        ),
        priority="LOW",
        recommendation=(
            "Do not optimize discount strategy from this dataset alone. "
            "Use controlled discount experiments or richer historical "
            "discount variation for future analysis."
        )
    )

# CREATE FINDINGS DATAFRAME

findings_df = pd.DataFrame(findings)
priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3 }
findings_df["priority_rank"] = (findings_df["priority"].map(priority_order))
findings_df = findings_df.sort_values("priority_rank").drop(columns=["priority_rank"])

# DISPLAY

print("***PROFITLEAK AI — BUSINESS FINDINGS***")
for i, row in findings_df.iterrows():
    print("\n")
    print(f"AREA: {row['area']}")
    print(f"PRIORITY: {row['priority']}")
    print(f"\nObservation:")
    print(row["observation"])
    print(f"\nRoot Cause:")
    print(row["root_cause"])
    print(f"\nFinancial Impact:")
    print(row["financial_impact"])
    print(f"\nRecommendation:")
    print(row["recommendation"])

# SAVE
findings_df.to_csv(OUTPUT_DIR / "business_findings.csv",index=False)

print("***BUSINESS FINDINGS ENGINE COMPLETE***")
print(f"Saved to: {OUTPUT_DIR / 'business_findings.csv'}")