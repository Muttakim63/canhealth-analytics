import os
import sqlite3
import pandas as pd

def main():
    print("--- Setting up CanHealth Analytics Database (SQLite/DuckDB compatible) ---")
    db_path = "/Users/shuprov630/canhealth-analytics/canhealth.db"
    data_dir = "/Users/shuprov630/canhealth-analytics/data"
    
    conn = sqlite3.connect(db_path)
    
    # Load CSV files into tables
    csv_tables = {
        'dim_hospitals': 'dim_hospitals.csv',
        'dim_periods': 'dim_periods.csv',
        'dim_procedures': 'dim_procedures.csv',
        'fact_financials': 'fact_financials.csv',
        'fact_wait_times': 'fact_wait_times.csv'
    }
    
    for table_name, csv_file in csv_tables.items():
        file_path = os.path.join(data_dir, csv_file)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Loaded {table_name}: {df.shape[0]} rows, {df.shape[1]} columns")
            
    conn.commit()
    conn.close()
    print(f"Database successfully generated at {db_path}!")

if __name__ == '__main__':
    main()
