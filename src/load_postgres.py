"""
src/load_postgres.py
====================
Loads generated CSVs into PostgreSQL using psycopg2.

Prerequisites:
  pip install psycopg2-binary
  PostgreSQL running locally (default port 5432)

Usage:
  python src/load_postgres.py
"""

import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DB",       "canhealth"),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASS",     "postgres"),
}

LOAD_ORDER = [
    ("data/dim_periods.csv",    "dim_periods"),
    ("data/dim_procedures.csv", "dim_procedures"),
    ("data/dim_hospitals.csv",  "dim_hospitals"),
    ("data/fact_wait_times.csv","fact_wait_times"),
    ("data/fact_financials.csv","fact_financials"),
]

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def create_database():
    """Create canhealth database if it doesn't exist."""
    cfg = {**DB_CONFIG, "dbname": "postgres"}
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_CONFIG["dbname"])))
        print(f"  Created database: {DB_CONFIG['dbname']}")
    cur.close()
    conn.close()

def run_schema():
    """Execute the schema SQL file."""
    with open("sql/01_schema.sql", "r") as f:
        schema_sql = f.read()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(schema_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("  ✔  Schema created")

def load_csv(filepath, table_name, conn):
    df = pd.read_csv(filepath)
    # Replace NaN with None for PostgreSQL compatibility
    df = df.where(pd.notna(df), None)
    cols = list(df.columns)
    values = [tuple(row) for row in df.itertuples(index=False, name=None)]

    cur = conn.cursor()
    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, cols))
    )
    execute_values(cur, insert_sql, values, page_size=1000)
    conn.commit()
    cur.close()
    print(f"  ✔  {table_name}: {len(df):,} rows loaded")

def main():
    print("Setting up PostgreSQL …")
    create_database()
    run_schema()

    conn = get_conn()
    print("\nLoading CSV files …")
    for filepath, table in LOAD_ORDER:
        load_csv(filepath, table, conn)
    conn.close()
    print("\n✔  All data loaded into PostgreSQL.")
    print(f"   Connect: psql -h {DB_CONFIG['host']} -U {DB_CONFIG['user']} -d {DB_CONFIG['dbname']}")

if __name__ == "__main__":
    main()
