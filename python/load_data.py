import pandas as pd
import psycopg2
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "profit_leak_ai",
    "user": "postgres",
    "password": "Jivika@27"
}

print("\n\n" + "***PROFITLEAK AI - POSTGRESQL DATA LOADER***")

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
tables = [
    ("customers", "customers.csv"),
    ("suppliers", "suppliers.csv"),
    ("products", "products.csv"),
    ("orders", "orders.csv"),
    ("returns", "returns.csv"),
    ("marketing_campaigns", "marketing_campaigns.csv"),
]

for table_name, file_name in tables:
    print(f"\nLoading {table_name}...")
    file_path = CLEANED_DIR / file_name
    df = pd.read_csv(file_path)
    for column in df.columns:
        if "date" in column:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%Y-%m-%d")
    columns = list(df.columns)
    column_names = ", ".join(f'"{column}"' for column in columns)
    rows = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in df.itertuples(index=False, name=None)
    ]
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"""
        INSERT INTO {table_name} ({column_names})
        VALUES ({placeholders})
    """
    cursor.executemany(insert_query, rows)
    conn.commit()
    print(f"Loaded {len(df):,} rows into {table_name}")

print("\n\n" + "***VERIFYING ROW COUNTS***")
for table_name, _ in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"{table_name:22} {count:,}")

cursor.close()
conn.close()

print("\n\n" + "***DATA LOADING COMPLETED***")
