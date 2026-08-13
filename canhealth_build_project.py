"""
canhealth_build_project.py
==========================
Run this single script to scaffold the entire CanHealth Analytics
Senior Data Analyst portfolio project.

Usage:
    python canhealth_build_project.py

Creates: data/, sql/, src/, notebooks/, dashboard/ directories
and writes every source file.
"""

import os

for d in ["data", "sql", "src", "notebooks", "dashboard"]:
    os.makedirs(d, exist_ok=True)
print("✔  Directories created")


# ─────────────────────────────────────────────────────────────────────────────
# src/generate_data.py
# ─────────────────────────────────────────────────────────────────────────────
GENERATE_DATA = '''"""
src/generate_data.py
====================
Generates a synthetic but realistic CIHI-modelled dataset with:
  - 150 Canadian hospitals across 13 provinces/territories
  - 8 priority procedures (matching real CIHI benchmarks)
  - 10 fiscal years (2014-15 through 2023-24)
  - ~180,000 wait time records in a star schema
  - Hospital financials and staffing data

Run: python src/generate_data.py
"""

import numpy as np
import pandas as pd
import os

RNG = np.random.default_rng(seed=2024)

# ── Dimension: Provinces ──────────────────────────────────────────────────────
PROVINCES = {
    "ON": {"name": "Ontario",               "weight": 0.38, "urban_rate": 0.87},
    "QC": {"name": "Quebec",                "weight": 0.23, "urban_rate": 0.81},
    "BC": {"name": "British Columbia",      "weight": 0.13, "urban_rate": 0.87},
    "AB": {"name": "Alberta",               "weight": 0.11, "urban_rate": 0.83},
    "MB": {"name": "Manitoba",              "weight": 0.04, "urban_rate": 0.72},
    "SK": {"name": "Saskatchewan",          "weight": 0.03, "urban_rate": 0.66},
    "NS": {"name": "Nova Scotia",           "weight": 0.03, "urban_rate": 0.55},
    "NB": {"name": "New Brunswick",         "weight": 0.02, "urban_rate": 0.56},
    "NL": {"name": "Newfoundland",          "weight": 0.01, "urban_rate": 0.60},
    "PE": {"name": "Prince Edward Island",  "weight": 0.004,"urban_rate": 0.47},
    "NT": {"name": "Northwest Territories", "weight": 0.001,"urban_rate": 0.46},
    "YT": {"name": "Yukon",                 "weight": 0.001,"urban_rate": 0.74},
    "NU": {"name": "Nunavut",               "weight": 0.001,"urban_rate": 0.32},
}

# ── Dimension: Procedures (real CIHI benchmarks) ──────────────────────────────
PROCEDURES = [
    {"procedure_id": 1, "code": "HIP_REP",  "name": "Hip Replacement",
     "category": "Orthopaedic",   "benchmark_50_days": 91,  "benchmark_90_days": 182,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 2, "code": "KNEE_REP", "name": "Knee Replacement",
     "category": "Orthopaedic",   "benchmark_50_days": 91,  "benchmark_90_days": 182,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 3, "code": "HIP_FRAC", "name": "Hip Fracture Repair",
     "category": "Orthopaedic",   "benchmark_50_days": 1,   "benchmark_90_days": 2,
     "complexity": "urgent",  "requires_specialist": True},
    {"procedure_id": 4, "code": "CATARACT", "name": "Cataract Surgery",
     "category": "Ophthalmology", "benchmark_50_days": 56,  "benchmark_90_days": 112,
     "complexity": "low",    "requires_specialist": True},
    {"procedure_id": 5, "code": "RAD_THER", "name": "Radiation Therapy",
     "category": "Oncology",      "benchmark_50_days": 14,  "benchmark_90_days": 28,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 6, "code": "BYPASS",   "name": "Cardiac Bypass Surgery",
     "category": "Cardiac",       "benchmark_50_days": 7,   "benchmark_90_days": 14,
     "complexity": "urgent",  "requires_specialist": True},
    {"procedure_id": 7, "code": "CANCER_S", "name": "Cancer Surgery",
     "category": "Oncology",      "benchmark_50_days": 14,  "benchmark_90_days": 28,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 8, "code": "MRI_SCAN", "name": "MRI Scan",
     "category": "Diagnostic",    "benchmark_50_days": 15,  "benchmark_90_days": 30,
     "complexity": "low",    "requires_specialist": False},
]

# ── Dimension: Fiscal Periods ─────────────────────────────────────────────────
FISCAL_YEARS = [
    {"period_id": i+1, "fiscal_year": 2014+i,
     "fiscal_year_label": f"{2014+i}-{str(2015+i)[2:]}",
     "is_covid_period": (2014+i) in [2020, 2021],
     "is_post_covid": (2014+i) in [2022, 2023]}
    for i in range(10)
]

# ── Hospital name components ───────────────────────────────────────────────────
HOSPITAL_PREFIXES = [
    "Royal", "St.", "General", "Regional", "Memorial", "University",
    "Community", "Mount", "Civic", "Victoria", "Queen's", "Sunnybrook",
    "North", "South", "East", "West", "Central", "Heritage", "Maple",
]
HOSPITAL_SUFFIXES = [
    "Hospital", "Medical Centre", "Health Centre", "Hospital & Health Sciences Centre",
    "General Hospital", "Regional Hospital", "Memorial Hospital",
]
CITY_NAMES = {
    "ON": ["Toronto","Ottawa","Hamilton","London","Kingston","Sudbury","Thunder Bay",
           "Windsor","Barrie","Brampton","Mississauga","Peterborough","Sault Ste. Marie"],
    "QC": ["Montreal","Quebec City","Laval","Gatineau","Sherbrooke","Saguenay",
           "Trois-Rivieres","Chicoutimi","Rimouski","Rouyn-Noranda"],
    "BC": ["Vancouver","Victoria","Surrey","Kelowna","Kamloops","Prince George",
           "Nanaimo","Abbotsford","Chilliwack","Cranbrook"],
    "AB": ["Calgary","Edmonton","Red Deer","Lethbridge","Medicine Hat","Grande Prairie",
           "Fort McMurray","Lloydminster"],
    "MB": ["Winnipeg","Brandon","Thompson","Portage la Prairie","Steinbach"],
    "SK": ["Saskatoon","Regina","Prince Albert","Moose Jaw","Swift Current"],
    "NS": ["Halifax","Sydney","Truro","New Glasgow","Kentville","Bridgewater"],
    "NB": ["Fredericton","Moncton","Saint John","Bathurst","Edmundston"],
    "NL": ["St. John's","Corner Brook","Gander","Grand Falls-Windsor","Labrador City"],
    "PE": ["Charlottetown","Summerside","Stratford"],
    "NT": ["Yellowknife","Hay River","Fort Smith"],
    "YT": ["Whitehorse","Dawson City"],
    "NU": ["Iqaluit","Rankin Inlet","Arviat"],
}
HEALTH_REGIONS = {
    "ON": ["Toronto Central","Central","East","West","North East","North West","South West"],
    "QC": ["Montreal","Capitale-Nationale","Estrie","Mauricie","Outaouais","Lanaudiere"],
    "BC": ["Fraser","Interior","Northern","Vancouver Coastal","Vancouver Island"],
    "AB": ["Calgary Zone","Edmonton Zone","Central Zone","North Zone","South Zone"],
    "MB": ["Winnipeg","Prairie Mountain","Southern Health","Northern Health","Interlake-Eastern"],
    "SK": ["Regina","Saskatoon","Far North","North","Central","South"],
    "NS": ["Central","Northern","Eastern","Western"],
    "NB": ["Horizon","Vitalite"],
    "NL": ["Eastern","Central","Western","Labrador-Grenfell"],
    "PE": ["Health PEI"],
    "NT": ["NTHSSA"],
    "YT": ["Yukon Health"],
    "NU": ["Nunavut Health"],
}

def generate_hospitals(n=150):
    rows = []
    province_codes = list(PROVINCES.keys())
    weights = [PROVINCES[p]["weight"] for p in province_codes]
    provinces_assigned = RNG.choice(province_codes, size=n, p=weights/np.array(weights).sum())

    for i, prov in enumerate(provinces_assigned):
        pinfo = PROVINCES[prov]
        is_urban = RNG.random() < pinfo["urban_rate"]
        hosp_type = RNG.choice(
            ["Teaching", "Community", "Rural", "Specialty"],
            p=[0.15, 0.55, 0.25, 0.05]
        )
        if not is_urban:
            hosp_type = "Rural"
        city = RNG.choice(CITY_NAMES.get(prov, [prov + " City"]))
        region = RNG.choice(HEALTH_REGIONS.get(prov, ["Regional"]))
        prefix = RNG.choice(HOSPITAL_PREFIXES)
        suffix = RNG.choice(HOSPITAL_SUFFIXES)

        bed_mu = {"Teaching": 450, "Community": 180, "Rural": 60, "Specialty": 120}[hosp_type]
        beds = max(20, int(RNG.normal(bed_mu, bed_mu * 0.3)))

        rows.append({
            "hospital_id":    i + 1,
            "hospital_name":  f"{prefix} {city} {suffix}",
            "province_code":  prov,
            "province_name":  pinfo["name"],
            "health_region":  region,
            "city":           city,
            "hospital_type":  hosp_type,
            "urban_rural":    "Urban" if is_urban else "Rural",
            "bed_count":      beds,
            "established_year": int(RNG.integers(1880, 1990)),
        })
    return pd.DataFrame(rows)

def generate_wait_times(hospitals_df, n_target=180_000):
    records = []
    record_id = 1

    for _, hosp in hospitals_df.iterrows():
        hid     = hosp["hospital_id"]
        prov    = hosp["province_code"]
        htype   = hosp["hospital_type"]
        beds    = hosp["bed_count"]
        is_rural= hosp["urban_rural"] == "Rural"

        # Not every hospital does every procedure
        eligible_procs = []
        for proc in PROCEDURES:
            if proc["complexity"] == "urgent":
                if beds >= 100:
                    eligible_procs.append(proc)
            elif proc["requires_specialist"] and htype == "Rural":
                if RNG.random() < 0.3:
                    eligible_procs.append(proc)
            else:
                eligible_procs.append(proc)

        for proc in eligible_procs:
            for period in FISCAL_YEARS:
                yr   = period["fiscal_year"]
                pid  = period["period_id"]

                # Volume: proportional to beds, with noise
                base_vol = max(5, int(beds * RNG.uniform(0.3, 1.2)))
                if proc["complexity"] == "urgent":
                    base_vol = max(20, int(beds * RNG.uniform(0.8, 1.5)))
                if period["is_covid_period"]:
                    # Elective procedures dropped ~40% during COVID
                    if proc["complexity"] != "urgent":
                        base_vol = int(base_vol * RNG.uniform(0.45, 0.70))
                if period["is_post_covid"]:
                    # Recovery surge
                    base_vol = int(base_vol * RNG.uniform(1.10, 1.35))

                patient_count = max(3, base_vol + int(RNG.normal(0, base_vol * 0.15)))

                # Wait time: based on benchmark, province performance, hospital type
                benchmark_90 = proc["benchmark_90_days"]
                benchmark_50 = proc["benchmark_50_days"]

                # Province performance multiplier (some provinces historically worse)
                prov_mult = {
                    "ON": 1.15, "QC": 1.30, "BC": 1.20, "AB": 1.05,
                    "MB": 1.25, "SK": 1.10, "NS": 1.35, "NB": 1.30,
                    "NL": 1.40, "PE": 1.45, "NT": 1.60, "YT": 1.55, "NU": 1.70,
                }[prov]

                rural_mult = 1.35 if is_rural else 1.0
                covid_mult = 1.45 if period["is_covid_period"] else 1.0
                trend_mult = 1.0 - (yr - 2014) * 0.008  # Slight improvement over time

                p90 = benchmark_90 * prov_mult * rural_mult * covid_mult * trend_mult
                p90 = max(benchmark_90 * 0.6, p90 * RNG.uniform(0.85, 1.20))
                p50 = p90 * RNG.uniform(0.45, 0.60)

                pct_benchmark = max(0, min(100,
                    100 * (benchmark_90 / p90) * RNG.uniform(0.80, 1.05)
                ))

                records.append({
                    "record_id":           record_id,
                    "hospital_id":         hid,
                    "procedure_id":        proc["procedure_id"],
                    "period_id":           pid,
                    "patient_count":       patient_count,
                    "p50_wait_days":       round(p50, 1),
                    "p90_wait_days":       round(p90, 1),
                    "pct_within_benchmark": round(pct_benchmark, 1),
                    "data_completeness":   RNG.choice(["Complete","Partial","Estimated"],
                                             p=[0.85, 0.10, 0.05]),
                })
                record_id += 1

                if len(records) >= n_target:
                    break
            if len(records) >= n_target:
                break
        if len(records) >= n_target:
            break

    return pd.DataFrame(records)

def generate_financials(hospitals_df):
    rows = []
    for _, hosp in hospitals_df.iterrows():
        hid   = hosp["hospital_id"]
        beds  = hosp["bed_count"]
        htype = hosp["hospital_type"]

        base_budget = beds * RNG.uniform(180_000, 280_000)  # ~$200k per bed/year

        for period in FISCAL_YEARS:
            yr  = period["fiscal_year"]
            pid = period["period_id"]

            inflation = 1.0 + (yr - 2014) * 0.028
            covid_surcharge = 1.12 if period["is_covid_period"] else 1.0
            budget = base_budget * inflation * covid_surcharge

            rows.append({
                "hospital_id":    hid,
                "period_id":      pid,
                "fiscal_year":    yr,
                "total_budget_cad":   round(budget, 0),
                "actual_spend_cad":   round(budget * RNG.uniform(0.93, 1.08), 0),
                "nursing_fte":    max(10, int(beds * RNG.uniform(1.2, 1.8))),
                "physician_fte":  max(3,  int(beds * RNG.uniform(0.15, 0.30))),
                "admin_fte":      max(5,  int(beds * RNG.uniform(0.20, 0.40))),
                "or_rooms":       max(1,  int(beds / RNG.uniform(25, 40))),
            })
    return pd.DataFrame(rows)

def main():
    os.makedirs("data", exist_ok=True)

    print("Generating hospitals …")
    hospitals = generate_hospitals(150)
    hospitals.to_csv("data/dim_hospitals.csv", index=False)
    print(f"  ✔  dim_hospitals.csv — {len(hospitals):,} rows")

    print("Generating procedures dimension …")
    procs_df = pd.DataFrame(PROCEDURES)
    procs_df.to_csv("data/dim_procedures.csv", index=False)
    print(f"  ✔  dim_procedures.csv — {len(procs_df):,} rows")

    print("Generating fiscal periods …")
    periods_df = pd.DataFrame(FISCAL_YEARS)
    periods_df.to_csv("data/dim_periods.csv", index=False)
    print(f"  ✔  dim_periods.csv — {len(periods_df):,} rows")

    print("Generating wait time records (~180k rows) …")
    wt = generate_wait_times(hospitals)
    wt.to_csv("data/fact_wait_times.csv", index=False)
    print(f"  ✔  fact_wait_times.csv — {len(wt):,} rows")

    print("Generating hospital financials …")
    fin = generate_financials(hospitals)
    fin.to_csv("data/fact_financials.csv", index=False)
    print(f"  ✔  fact_financials.csv — {len(fin):,} rows")

    print("\\nDataset summary:")
    print(f"  Hospitals:       {len(hospitals):,}")
    print(f"  Procedures:      {len(procs_df):,}")
    print(f"  Fiscal periods:  {len(periods_df):,}")
    print(f"  Wait records:    {len(wt):,}")
    print(f"  Financial rows:  {len(fin):,}")

if __name__ == "__main__":
    main()
'''

with open("src/generate_data.py", "w") as f:
    f.write(GENERATE_DATA)
print("✔  src/generate_data.py")


# ─────────────────────────────────────────────────────────────────────────────
# src/load_postgres.py
# ─────────────────────────────────────────────────────────────────────────────
LOAD_PG = '''"""
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
    """Create canhealth database if it doesn\'t exist."""
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
    print("\\nLoading CSV files …")
    for filepath, table in LOAD_ORDER:
        load_csv(filepath, table, conn)
    conn.close()
    print("\\n✔  All data loaded into PostgreSQL.")
    print(f"   Connect: psql -h {DB_CONFIG[\'host\']} -U {DB_CONFIG[\'user\']} -d {DB_CONFIG[\'dbname\']}")

if __name__ == "__main__":
    main()
'''

with open("src/load_postgres.py", "w") as f:
    f.write(LOAD_PG)
print("✔  src/load_postgres.py")


# ─────────────────────────────────────────────────────────────────────────────
# sql/01_schema.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_01 = '''-- ============================================================
-- 01_schema.sql
-- CanHealth Analytics — Database Schema
-- Star schema: 3 dimension tables + 2 fact tables
-- ============================================================

-- Drop in reverse dependency order
DROP TABLE IF EXISTS fact_financials    CASCADE;
DROP TABLE IF EXISTS fact_wait_times    CASCADE;
DROP TABLE IF EXISTS dim_hospitals      CASCADE;
DROP TABLE IF EXISTS dim_procedures     CASCADE;
DROP TABLE IF EXISTS dim_periods        CASCADE;

-- ── Dimension: Fiscal Periods ────────────────────────────────────────────────
CREATE TABLE dim_periods (
    period_id           SERIAL PRIMARY KEY,
    fiscal_year         SMALLINT    NOT NULL,
    fiscal_year_label   VARCHAR(10) NOT NULL,   -- e.g. "2019-20"
    is_covid_period     BOOLEAN     NOT NULL DEFAULT FALSE,
    is_post_covid       BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_period UNIQUE (fiscal_year)
);

-- ── Dimension: Procedures ────────────────────────────────────────────────────
CREATE TABLE dim_procedures (
    procedure_id        SERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,
    name                VARCHAR(80) NOT NULL,
    category            VARCHAR(40) NOT NULL,
    benchmark_50_days   SMALLINT    NOT NULL,
    benchmark_90_days   SMALLINT    NOT NULL,
    complexity          VARCHAR(10) NOT NULL CHECK (complexity IN (\'low\',\'high\',\'urgent\')),
    requires_specialist BOOLEAN     NOT NULL DEFAULT TRUE
);

-- ── Dimension: Hospitals ─────────────────────────────────────────────────────
CREATE TABLE dim_hospitals (
    hospital_id         SERIAL PRIMARY KEY,
    hospital_name       VARCHAR(120) NOT NULL,
    province_code       CHAR(2)      NOT NULL,
    province_name       VARCHAR(40)  NOT NULL,
    health_region       VARCHAR(60)  NOT NULL,
    city                VARCHAR(60)  NOT NULL,
    hospital_type       VARCHAR(20)  NOT NULL
        CHECK (hospital_type IN (\'Teaching\',\'Community\',\'Rural\',\'Specialty\')),
    urban_rural         VARCHAR(10)  NOT NULL CHECK (urban_rural IN (\'Urban\',\'Rural\')),
    bed_count           SMALLINT     NOT NULL CHECK (bed_count > 0),
    established_year    SMALLINT
);

-- ── Fact: Wait Times ─────────────────────────────────────────────────────────
CREATE TABLE fact_wait_times (
    record_id               BIGSERIAL   PRIMARY KEY,
    hospital_id             INT         NOT NULL REFERENCES dim_hospitals(hospital_id),
    procedure_id            INT         NOT NULL REFERENCES dim_procedures(procedure_id),
    period_id               INT         NOT NULL REFERENCES dim_periods(period_id),
    patient_count           INT         NOT NULL CHECK (patient_count >= 0),
    p50_wait_days           NUMERIC(7,1),
    p90_wait_days           NUMERIC(7,1),
    pct_within_benchmark    NUMERIC(5,1) CHECK (pct_within_benchmark BETWEEN 0 AND 100),
    data_completeness       VARCHAR(10)  DEFAULT \'Complete\'
);

-- ── Fact: Financials ─────────────────────────────────────────────────────────
CREATE TABLE fact_financials (
    hospital_id         INT         NOT NULL REFERENCES dim_hospitals(hospital_id),
    period_id           INT         NOT NULL REFERENCES dim_periods(period_id),
    fiscal_year         SMALLINT    NOT NULL,
    total_budget_cad    BIGINT,
    actual_spend_cad    BIGINT,
    nursing_fte         SMALLINT,
    physician_fte       SMALLINT,
    admin_fte           SMALLINT,
    or_rooms            SMALLINT,
    PRIMARY KEY (hospital_id, period_id)
);

-- ── Indexes for query performance ─────────────────────────────────────────────
-- High-cardinality foreign keys on the fact tables
CREATE INDEX idx_wt_hospital    ON fact_wait_times (hospital_id);
CREATE INDEX idx_wt_procedure   ON fact_wait_times (procedure_id);
CREATE INDEX idx_wt_period      ON fact_wait_times (period_id);
CREATE INDEX idx_wt_pct_bench   ON fact_wait_times (pct_within_benchmark);
CREATE INDEX idx_wt_p90         ON fact_wait_times (p90_wait_days);
CREATE INDEX idx_fin_hospital   ON fact_financials (hospital_id);
CREATE INDEX idx_fin_period     ON fact_financials (period_id);

-- Composite index for the most common analytical join pattern
CREATE INDEX idx_wt_hosp_proc_period ON fact_wait_times (hospital_id, procedure_id, period_id);

-- Province filtering is very common in healthcare analytics
CREATE INDEX idx_hosp_province  ON dim_hospitals (province_code);
CREATE INDEX idx_hosp_type      ON dim_hospitals (hospital_type);

-- ── Comments (good practice for team environments) ────────────────────────────
COMMENT ON TABLE fact_wait_times IS
    \'Primary fact table. One row per hospital-procedure-year combination. \'
    \'Modelled after CIHI Wait Times for Priority Procedures dataset.\';

COMMENT ON COLUMN fact_wait_times.p90_wait_days IS
    \'90th percentile wait time in days. CIHI benchmark is measured at this percentile.\';

COMMENT ON COLUMN fact_wait_times.pct_within_benchmark IS
    \'Percentage of patients who received care within the CIHI benchmark target.\';
'''

with open("sql/01_schema.sql", "w") as f:
    f.write(SQL_01)
print("✔  sql/01_schema.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/02_basic_exploration.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_02 = '''-- ============================================================
-- 02_basic_exploration.sql
-- Level: Foundational
-- Concepts: SELECT, WHERE, GROUP BY, HAVING, ORDER BY,
--           DISTINCT, COUNT, AVG, MIN, MAX, ROUND
-- ============================================================


-- ── 1. How many hospitals are in each province? ───────────────────────────────
SELECT
    province_code,
    province_name,
    COUNT(*)                        AS total_hospitals,
    SUM(bed_count)                  AS total_beds,
    ROUND(AVG(bed_count), 0)        AS avg_beds_per_hospital,
    MIN(bed_count)                  AS smallest_hospital_beds,
    MAX(bed_count)                  AS largest_hospital_beds
FROM dim_hospitals
GROUP BY province_code, province_name
ORDER BY total_hospitals DESC;


-- ── 2. What is the breakdown of hospitals by type and urban/rural? ────────────
SELECT
    hospital_type,
    urban_rural,
    COUNT(*)                        AS hospital_count,
    ROUND(AVG(bed_count), 0)        AS avg_beds,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM dim_hospitals
GROUP BY hospital_type, urban_rural
ORDER BY hospital_type, urban_rural;


-- ── 3. Which procedures have the longest average 90th-percentile wait? ────────
SELECT
    p.name                          AS procedure_name,
    p.category,
    p.benchmark_90_days,
    ROUND(AVG(wt.p90_wait_days), 1) AS avg_p90_wait,
    ROUND(AVG(wt.p90_wait_days) - p.benchmark_90_days, 1) AS avg_days_over_benchmark,
    ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_pct_within_benchmark,
    SUM(wt.patient_count)           AS total_patients
FROM fact_wait_times   wt
JOIN dim_procedures    p  ON p.procedure_id = wt.procedure_id
GROUP BY p.procedure_id, p.name, p.category, p.benchmark_90_days
ORDER BY avg_p90_wait DESC;


-- ── 4. Annual national summary — how have wait times trended? ─────────────────
SELECT
    dp.fiscal_year_label,
    dp.is_covid_period,
    COUNT(DISTINCT wt.hospital_id)  AS reporting_hospitals,
    SUM(wt.patient_count)           AS total_patients,
    ROUND(AVG(wt.p90_wait_days), 1) AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_pct_within_benchmark
FROM fact_wait_times   wt
JOIN dim_periods       dp ON dp.period_id = wt.period_id
GROUP BY dp.period_id, dp.fiscal_year_label, dp.is_covid_period
ORDER BY dp.fiscal_year_label;


-- ── 5. Which provinces CONSISTENTLY miss benchmarks? (HAVING filter) ──────────
SELECT
    h.province_code,
    h.province_name,
    COUNT(*)                             AS total_records,
    ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_benchmark_pct,
    COUNT(CASE WHEN wt.pct_within_benchmark < 70 THEN 1 END) AS records_below_70pct,
    ROUND(100.0 * COUNT(CASE WHEN wt.pct_within_benchmark < 70 THEN 1 END)
          / COUNT(*), 1)                 AS pct_records_below_threshold
FROM fact_wait_times   wt
JOIN dim_hospitals     h  ON h.hospital_id = wt.hospital_id
GROUP BY h.province_code, h.province_name
HAVING AVG(wt.pct_within_benchmark) < 85
ORDER BY avg_benchmark_pct ASC;


-- ── 6. COVID impact: compare avg wait times pre, during, post COVID ───────────
SELECT
    CASE
        WHEN dp.is_covid_period THEN \'During COVID (2020-21)\'
        WHEN dp.is_post_covid   THEN \'Post-COVID (2022-23)\'
        ELSE                         \'Pre-COVID (2014-19)\'
    END                              AS era,
    ROUND(AVG(wt.p90_wait_days), 1)  AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_pct_within_benchmark,
    SUM(wt.patient_count)            AS total_patients,
    COUNT(DISTINCT wt.hospital_id)   AS hospitals_reporting
FROM fact_wait_times   wt
JOIN dim_periods       dp ON dp.period_id = wt.period_id
GROUP BY
    dp.is_covid_period,
    dp.is_post_covid
ORDER BY era;
'''

with open("sql/02_basic_exploration.sql", "w") as f:
    f.write(SQL_02)
print("✔  sql/02_basic_exploration.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/03_joins_aggregations.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_03 = '''-- ============================================================
-- 03_joins_aggregations.sql
-- Level: Intermediate
-- Concepts: INNER JOIN, LEFT JOIN, multi-table joins,
--           conditional aggregation (CASE WHEN inside SUM/COUNT),
--           FILTER clause, COALESCE, NULL handling
-- ============================================================


-- ── 1. Full denormalized view of a sample of wait time records ────────────────
--    Shows how to join all 3 dimension tables to the fact table at once.
SELECT
    wt.record_id,
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    h.urban_rural,
    p.name                  AS procedure_name,
    p.category              AS procedure_category,
    p.benchmark_90_days,
    dp.fiscal_year_label,
    dp.is_covid_period,
    wt.patient_count,
    wt.p90_wait_days,
    wt.pct_within_benchmark,
    -- Derived column: did this record meet the benchmark?
    CASE
        WHEN wt.pct_within_benchmark >= 90 THEN \'Met\'
        WHEN wt.pct_within_benchmark >= 70 THEN \'Near-Miss\'
        ELSE                                    \'Missed\'
    END                     AS benchmark_status
FROM fact_wait_times   wt
INNER JOIN dim_hospitals   h  ON h.hospital_id  = wt.hospital_id
INNER JOIN dim_procedures  p  ON p.procedure_id = wt.procedure_id
INNER JOIN dim_periods     dp ON dp.period_id   = wt.period_id
ORDER BY wt.record_id
LIMIT 100;


-- ── 2. Hospital performance scorecard (multi-dimension join + CASE agg) ────────
--    For each hospital: volume, avg wait, benchmark rate, and a letter grade
SELECT
    h.hospital_id,
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    h.urban_rural,
    h.bed_count,
    -- Volume metrics
    SUM(wt.patient_count)                               AS total_patients_all_years,
    COUNT(DISTINCT wt.procedure_id)                     AS procedures_offered,
    COUNT(DISTINCT wt.period_id)                        AS years_reporting,
    -- Wait time metrics
    ROUND(AVG(wt.p90_wait_days), 1)                    AS overall_avg_p90,
    ROUND(AVG(wt.pct_within_benchmark), 1)             AS overall_benchmark_pct,
    -- Conditional aggregation: count records in each performance band
    COUNT(wt.record_id)
        FILTER (WHERE wt.pct_within_benchmark >= 90)    AS records_met_benchmark,
    COUNT(wt.record_id)
        FILTER (WHERE wt.pct_within_benchmark BETWEEN 70 AND 89.9) AS records_near_miss,
    COUNT(wt.record_id)
        FILTER (WHERE wt.pct_within_benchmark < 70)     AS records_missed_benchmark,
    -- Composite performance grade
    CASE
        WHEN AVG(wt.pct_within_benchmark) >= 90 THEN \'A\'
        WHEN AVG(wt.pct_within_benchmark) >= 80 THEN \'B\'
        WHEN AVG(wt.pct_within_benchmark) >= 70 THEN \'C\'
        WHEN AVG(wt.pct_within_benchmark) >= 60 THEN \'D\'
        ELSE                                          \'F\'
    END                                                 AS performance_grade
FROM fact_wait_times   wt
INNER JOIN dim_hospitals h ON h.hospital_id = wt.hospital_id
GROUP BY
    h.hospital_id, h.hospital_name, h.province_code,
    h.hospital_type, h.urban_rural, h.bed_count
ORDER BY overall_benchmark_pct DESC;


-- ── 3. Procedure-province cross-tab: which combos are worst? ──────────────────
SELECT
    h.province_code,
    p.name                              AS procedure_name,
    COUNT(*)                            AS record_count,
    SUM(wt.patient_count)               AS total_patients,
    ROUND(AVG(wt.p90_wait_days), 1)     AS avg_p90_days,
    p.benchmark_90_days                 AS target_days,
    ROUND(AVG(wt.p90_wait_days) / p.benchmark_90_days * 100 - 100, 1)
                                        AS pct_over_benchmark,
    ROUND(AVG(wt.pct_within_benchmark), 1) AS pct_patients_within_target
FROM fact_wait_times   wt
JOIN dim_hospitals     h  ON h.hospital_id  = wt.hospital_id
JOIN dim_procedures    p  ON p.procedure_id = wt.procedure_id
GROUP BY h.province_code, p.procedure_id, p.name, p.benchmark_90_days
ORDER BY pct_over_benchmark DESC
LIMIT 30;


-- ── 4. LEFT JOIN: hospitals with no financial data (data quality check) ────────
--    LEFT JOIN shows ALL hospitals, including those without financial records
SELECT
    h.hospital_id,
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    COUNT(f.hospital_id)    AS financial_records,
    -- COALESCE handles NULLs from the LEFT JOIN
    COALESCE(ROUND(AVG(f.total_budget_cad / 1000000.0), 2), 0) AS avg_budget_millions,
    CASE
        WHEN COUNT(f.hospital_id) = 0 THEN \'No financial data\'
        WHEN COUNT(f.hospital_id) < 5 THEN \'Partial data\'
        ELSE \'Complete\'
    END                     AS data_status
FROM dim_hospitals         h
LEFT JOIN fact_financials  f ON f.hospital_id = h.hospital_id
GROUP BY h.hospital_id, h.hospital_name, h.province_code, h.hospital_type
ORDER BY financial_records ASC;


-- ── 5. Budget efficiency: spend per patient treated ────────────────────────────
SELECT
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    dp.fiscal_year_label,
    f.total_budget_cad,
    f.actual_spend_cad,
    SUM(wt.patient_count)   AS patients_treated,
    -- Spend per patient
    CASE
        WHEN SUM(wt.patient_count) > 0
        THEN ROUND(f.actual_spend_cad::NUMERIC / SUM(wt.patient_count), 0)
        ELSE NULL
    END                     AS spend_per_patient_cad,
    -- Budget variance
    ROUND((f.actual_spend_cad - f.total_budget_cad)::NUMERIC
          / f.total_budget_cad * 100, 2) AS budget_variance_pct,
    CASE
        WHEN f.actual_spend_cad > f.total_budget_cad THEN \'Over Budget\'
        ELSE \'Within Budget\'
    END                     AS budget_status
FROM fact_financials       f
JOIN dim_hospitals         h  ON h.hospital_id = f.hospital_id
JOIN dim_periods           dp ON dp.period_id  = f.period_id
LEFT JOIN fact_wait_times  wt ON wt.hospital_id = f.hospital_id
                              AND wt.period_id  = f.period_id
GROUP BY
    h.hospital_name, h.province_code, h.hospital_type,
    dp.fiscal_year_label, f.total_budget_cad, f.actual_spend_cad
ORDER BY spend_per_patient_cad DESC NULLS LAST
LIMIT 50;
'''

with open("sql/03_joins_aggregations.sql", "w") as f:
    f.write(SQL_03)
print("✔  sql/03_joins_aggregations.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/04_ctes_subqueries.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_04 = '''-- ============================================================
-- 04_ctes_subqueries.sql
-- Level: Intermediate → Advanced
-- Concepts: WITH (CTEs), chained CTEs, correlated subqueries,
--           EXISTS / NOT EXISTS, scalar subqueries, derived tables
-- ============================================================


-- ── 1. Chained CTEs: Provincial performance tiers ─────────────────────────────
--    Step 1: aggregate per province
--    Step 2: calculate national average as a scalar
--    Step 3: classify provinces relative to national average
WITH provincial_avg AS (
    SELECT
        h.province_code,
        h.province_name,
        ROUND(AVG(wt.p90_wait_days), 1)           AS avg_p90_wait,
        ROUND(AVG(wt.pct_within_benchmark), 1)    AS avg_benchmark_pct,
        SUM(wt.patient_count)                     AS total_patients,
        COUNT(DISTINCT h.hospital_id)             AS hospital_count
    FROM fact_wait_times wt
    JOIN dim_hospitals   h ON h.hospital_id = wt.hospital_id
    GROUP BY h.province_code, h.province_name
),
national_benchmark AS (
    SELECT
        AVG(avg_p90_wait)           AS national_avg_p90,
        AVG(avg_benchmark_pct)      AS national_avg_benchmark_pct
    FROM provincial_avg
),
classified AS (
    SELECT
        pa.province_code,
        pa.province_name,
        pa.avg_p90_wait,
        pa.avg_benchmark_pct,
        pa.total_patients,
        pa.hospital_count,
        nb.national_avg_p90,
        nb.national_avg_benchmark_pct,
        ROUND(pa.avg_p90_wait - nb.national_avg_p90, 1)   AS days_vs_national_avg,
        CASE
            WHEN pa.avg_benchmark_pct >= nb.national_avg_benchmark_pct + 5
                THEN \'Top Performer\'
            WHEN pa.avg_benchmark_pct >= nb.national_avg_benchmark_pct - 2
                THEN \'On Par\'
            WHEN pa.avg_benchmark_pct >= nb.national_avg_benchmark_pct - 10
                THEN \'Below Average\'
            ELSE \'Needs Attention\'
        END                                                AS performance_tier
    FROM provincial_avg   pa
    CROSS JOIN national_benchmark nb
)
SELECT *
FROM classified
ORDER BY avg_benchmark_pct DESC;


-- ── 2. CTE + self-reference: find hospitals that IMPROVED the most ─────────────
WITH first_year AS (
    SELECT
        wt.hospital_id,
        ROUND(AVG(wt.p90_wait_days), 1)        AS p90_2014,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS bench_2014
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    WHERE dp.fiscal_year = 2014
    GROUP BY wt.hospital_id
),
latest_year AS (
    SELECT
        wt.hospital_id,
        ROUND(AVG(wt.p90_wait_days), 1)        AS p90_2023,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS bench_2023
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    WHERE dp.fiscal_year = 2023
    GROUP BY wt.hospital_id
),
improvement AS (
    SELECT
        f.hospital_id,
        f.p90_2014,
        l.p90_2023,
        ROUND(f.p90_2014 - l.p90_2023, 1)     AS p90_days_reduced,
        f.bench_2014,
        l.bench_2023,
        ROUND(l.bench_2023 - f.bench_2014, 1) AS benchmark_pct_gained
    FROM first_year  f
    JOIN latest_year l USING (hospital_id)
    -- Only include hospitals with data in both years
)
SELECT
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    i.p90_2014,
    i.p90_2023,
    i.p90_days_reduced,
    i.bench_2014,
    i.bench_2023,
    i.benchmark_pct_gained,
    CASE
        WHEN i.benchmark_pct_gained >= 15 THEN \'Major Improvement\'
        WHEN i.benchmark_pct_gained >= 5  THEN \'Moderate Improvement\'
        WHEN i.benchmark_pct_gained >= 0  THEN \'Stable\'
        ELSE \'Declined\'
    END AS improvement_category
FROM improvement    i
JOIN dim_hospitals  h ON h.hospital_id = i.hospital_id
ORDER BY benchmark_pct_gained DESC
LIMIT 20;


-- ── 3. Correlated subquery: hospitals above their PROVINCIAL average ───────────
SELECT
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    ROUND(AVG(wt.p90_wait_days), 1)     AS hospital_avg_p90,
    -- Correlated subquery: recalculates for each province
    (
        SELECT ROUND(AVG(wt2.p90_wait_days), 1)
        FROM fact_wait_times wt2
        JOIN dim_hospitals   h2 ON h2.hospital_id = wt2.hospital_id
        WHERE h2.province_code = h.province_code
    )                                   AS provincial_avg_p90,
    ROUND(
        AVG(wt.p90_wait_days) - (
            SELECT AVG(wt2.p90_wait_days)
            FROM fact_wait_times wt2
            JOIN dim_hospitals   h2 ON h2.hospital_id = wt2.hospital_id
            WHERE h2.province_code = h.province_code
        ), 1
    )                                   AS days_vs_province_avg
FROM fact_wait_times wt
JOIN dim_hospitals   h ON h.hospital_id = wt.hospital_id
GROUP BY h.hospital_id, h.hospital_name, h.province_code, h.hospital_type
HAVING AVG(wt.p90_wait_days) > (
    SELECT AVG(wt2.p90_wait_days)
    FROM fact_wait_times wt2
    JOIN dim_hospitals   h2 ON h2.hospital_id = wt2.hospital_id
    WHERE h2.province_code = h.province_code
)
ORDER BY days_vs_province_avg DESC
LIMIT 30;


-- ── 4. EXISTS: hospitals that offer BOTH high-risk orthopaedic procedures ────────
SELECT
    h.hospital_name,
    h.province_code,
    h.hospital_type,
    h.bed_count
FROM dim_hospitals h
WHERE
    EXISTS (
        SELECT 1 FROM fact_wait_times wt
        JOIN dim_procedures p ON p.procedure_id = wt.procedure_id
        WHERE wt.hospital_id = h.hospital_id AND p.code = \'HIP_REP\'
    )
    AND EXISTS (
        SELECT 1 FROM fact_wait_times wt
        JOIN dim_procedures p ON p.procedure_id = wt.procedure_id
        WHERE wt.hospital_id = h.hospital_id AND p.code = \'KNEE_REP\'
    )
ORDER BY h.province_code, h.hospital_name;


-- ── 5. Recursive-style CTE: fiscal year cumulative patients ───────────────────
WITH yearly_national AS (
    SELECT
        dp.fiscal_year,
        dp.fiscal_year_label,
        SUM(wt.patient_count) AS annual_patients
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    GROUP BY dp.fiscal_year, dp.fiscal_year_label
),
cumulative AS (
    SELECT
        fiscal_year,
        fiscal_year_label,
        annual_patients,
        SUM(annual_patients) OVER (ORDER BY fiscal_year
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_patients,
        ROUND(100.0 * annual_patients /
              SUM(annual_patients) OVER (), 2)                AS pct_of_decade_total
    FROM yearly_national
)
SELECT *
FROM cumulative
ORDER BY fiscal_year;
'''

with open("sql/04_ctes_subqueries.sql", "w") as f:
    f.write(SQL_04)
print("✔  sql/04_ctes_subqueries.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/05_window_functions.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_05 = '''-- ============================================================
-- 05_window_functions.sql
-- Level: Advanced
-- Concepts: ROW_NUMBER, RANK, DENSE_RANK, NTILE,
--           LAG, LEAD, FIRST_VALUE, LAST_VALUE,
--           SUM/AVG/COUNT OVER (PARTITION BY ... ORDER BY ...),
--           frame clauses (ROWS BETWEEN)
-- ============================================================
-- Window functions compute a value ACROSS a set of rows related
-- to the current row WITHOUT collapsing them (unlike GROUP BY).


-- ── 1. RANK vs DENSE_RANK vs ROW_NUMBER — differences illustrated ─────────────
--    Rank hospitals by wait time within each province/procedure.
--    RANK:       ties get same rank, next rank skips (1,1,3)
--    DENSE_RANK: ties get same rank, no skipping (1,1,2)
--    ROW_NUMBER: always unique, arbitrary for ties (1,2,3)
WITH hospital_summary AS (
    SELECT
        h.hospital_id,
        h.hospital_name,
        h.province_code,
        p.name                              AS procedure_name,
        ROUND(AVG(wt.p90_wait_days), 1)    AS avg_p90_wait
    FROM fact_wait_times wt
    JOIN dim_hospitals   h ON h.hospital_id  = wt.hospital_id
    JOIN dim_procedures  p ON p.procedure_id = wt.procedure_id
    WHERE p.code = \'HIP_REP\'
    GROUP BY h.hospital_id, h.hospital_name, h.province_code, p.name
)
SELECT
    hospital_name,
    province_code,
    avg_p90_wait,
    RANK()        OVER (PARTITION BY province_code ORDER BY avg_p90_wait DESC) AS rank_in_province,
    DENSE_RANK()  OVER (PARTITION BY province_code ORDER BY avg_p90_wait DESC) AS dense_rank_in_province,
    ROW_NUMBER()  OVER (PARTITION BY province_code ORDER BY avg_p90_wait DESC) AS row_num_in_province,
    -- National rank
    RANK()        OVER (ORDER BY avg_p90_wait DESC)                             AS national_rank
FROM hospital_summary
ORDER BY province_code, avg_p90_wait DESC;


-- ── 2. LAG / LEAD: Year-over-year wait time change ────────────────────────────
WITH prov_year AS (
    SELECT
        h.province_code,
        dp.fiscal_year,
        dp.fiscal_year_label,
        ROUND(AVG(wt.p90_wait_days), 1)    AS avg_p90_wait,
        SUM(wt.patient_count)              AS total_patients
    FROM fact_wait_times wt
    JOIN dim_hospitals   h  ON h.hospital_id = wt.hospital_id
    JOIN dim_periods     dp ON dp.period_id  = wt.period_id
    GROUP BY h.province_code, dp.fiscal_year, dp.fiscal_year_label
)
SELECT
    province_code,
    fiscal_year_label,
    avg_p90_wait,
    -- LAG: look back 1 year
    LAG(avg_p90_wait, 1) OVER (
        PARTITION BY province_code
        ORDER BY fiscal_year
    )                                      AS prev_year_p90,
    -- Change from previous year
    ROUND(
        avg_p90_wait - LAG(avg_p90_wait, 1) OVER (
            PARTITION BY province_code ORDER BY fiscal_year
        ), 1
    )                                      AS yoy_change_days,
    -- LEAD: look forward 1 year (useful for forecasting context)
    LEAD(avg_p90_wait, 1) OVER (
        PARTITION BY province_code
        ORDER BY fiscal_year
    )                                      AS next_year_p90,
    total_patients
FROM prov_year
ORDER BY province_code, fiscal_year;


-- ── 3. Moving average: 3-year rolling average to smooth COVID noise ───────────
WITH national_yearly AS (
    SELECT
        dp.fiscal_year,
        dp.fiscal_year_label,
        ROUND(AVG(wt.p90_wait_days), 1) AS avg_p90_wait
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    GROUP BY dp.fiscal_year, dp.fiscal_year_label
)
SELECT
    fiscal_year_label,
    avg_p90_wait                                           AS actual_p90_wait,
    -- 3-year centred moving average
    ROUND(AVG(avg_p90_wait) OVER (
        ORDER BY fiscal_year
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 1)                                                  AS rolling_3yr_avg,
    -- Cumulative average from start of dataset
    ROUND(AVG(avg_p90_wait) OVER (
        ORDER BY fiscal_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 1)                                                  AS cumulative_avg,
    -- Running total patients
    SUM(SUM(wt2.patient_count)) OVER (              -- double aggregation pattern
        ORDER BY dp.fiscal_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                      AS running_total_patients
FROM national_yearly ny
-- Note: need to re-join for running total — shown for illustration
JOIN (SELECT period_id, patient_count FROM fact_wait_times) wt2_raw
    ON TRUE   -- simplified for illustration; use a proper CTE in production
JOIN dim_periods dp ON dp.fiscal_year = ny.fiscal_year
                   AND dp.period_id   = wt2_raw.period_id
GROUP BY ny.fiscal_year, ny.fiscal_year_label, ny.avg_p90_wait
ORDER BY ny.fiscal_year;


-- ── 4. NTILE: Quartile analysis — volume vs performance ───────────────────────
WITH hospital_10yr_summary AS (
    SELECT
        h.hospital_id,
        h.hospital_name,
        h.province_code,
        h.hospital_type,
        h.bed_count,
        SUM(wt.patient_count)               AS total_patients,
        ROUND(AVG(wt.p90_wait_days), 1)     AS avg_p90_wait,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_benchmark_pct
    FROM fact_wait_times wt
    JOIN dim_hospitals   h ON h.hospital_id = wt.hospital_id
    GROUP BY h.hospital_id, h.hospital_name, h.province_code,
             h.hospital_type, h.bed_count
    HAVING COUNT(*) >= 20  -- Only hospitals with sufficient data
)
SELECT
    hospital_name,
    province_code,
    hospital_type,
    total_patients,
    avg_p90_wait,
    avg_benchmark_pct,
    -- Volume quartile: 1=lowest volume, 4=highest
    NTILE(4) OVER (ORDER BY total_patients)         AS volume_quartile,
    -- Wait time quartile: 1=fastest (best), 4=slowest (worst)
    NTILE(4) OVER (ORDER BY avg_p90_wait)           AS wait_quartile,
    -- Benchmark quartile: 4=best performance, 1=worst
    NTILE(4) OVER (ORDER BY avg_benchmark_pct DESC) AS performance_quartile,
    -- High volume + poor performance = most critical to fix
    CASE
        WHEN NTILE(4) OVER (ORDER BY total_patients)         = 4
         AND NTILE(4) OVER (ORDER BY avg_benchmark_pct DESC) = 1
        THEN \'High Priority — High Volume, Low Performance\'
        WHEN NTILE(4) OVER (ORDER BY total_patients)         = 4
         AND NTILE(4) OVER (ORDER BY avg_benchmark_pct DESC) = 4
        THEN \'Model Hospital — High Volume, High Performance\'
        ELSE \'Standard\'
    END AS strategic_classification
FROM hospital_10yr_summary
ORDER BY total_patients DESC;


-- ── 5. FIRST_VALUE / LAST_VALUE: compare each year to province best year ──────
WITH prov_year AS (
    SELECT
        h.province_code,
        dp.fiscal_year,
        dp.fiscal_year_label,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS avg_benchmark_pct
    FROM fact_wait_times wt
    JOIN dim_hospitals   h  ON h.hospital_id = wt.hospital_id
    JOIN dim_periods     dp ON dp.period_id  = wt.period_id
    GROUP BY h.province_code, dp.fiscal_year, dp.fiscal_year_label
)
SELECT
    province_code,
    fiscal_year_label,
    avg_benchmark_pct,
    FIRST_VALUE(avg_benchmark_pct) OVER (
        PARTITION BY province_code
        ORDER BY avg_benchmark_pct DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                              AS province_best_ever,
    ROUND(
        avg_benchmark_pct -
        FIRST_VALUE(avg_benchmark_pct) OVER (
            PARTITION BY province_code
            ORDER BY avg_benchmark_pct DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ), 1
    )                                              AS gap_to_best_year
FROM prov_year
ORDER BY province_code, fiscal_year;
'''

with open("sql/05_window_functions.sql", "w") as f:
    f.write(SQL_05)
print("✔  sql/05_window_functions.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/06_advanced_analytics.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_06 = '''-- ============================================================
-- 06_advanced_analytics.sql
-- Level: Senior DA
-- Concepts: Percentile functions, cohort analysis,
--           pivot-style aggregation, STRING_AGG, GENERATE_SERIES,
--           complex multi-CTE analytical queries
-- ============================================================


-- ── 1. Statistical spread: percentile wait times by procedure ─────────────────
--    PERCENTILE_CONT: interpolated (continuous)
--    PERCENTILE_DISC: actual data value (discrete)
SELECT
    p.name                              AS procedure_name,
    p.category,
    p.benchmark_90_days,
    ROUND(MIN(wt.p90_wait_days), 1)     AS min_p90,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC, 1)
                                        AS q1_p90,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC, 1)
                                        AS median_p90,
    ROUND(AVG(wt.p90_wait_days), 1)     AS mean_p90,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC, 1)
                                        AS q3_p90,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC, 1)
                                        AS p90_of_p90,
    ROUND(MAX(wt.p90_wait_days), 1)     AS max_p90,
    -- Interquartile range
    ROUND(
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC -
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY wt.p90_wait_days)::NUMERIC
    , 1)                                AS iqr_days,
    COUNT(*)                            AS observations
FROM fact_wait_times wt
JOIN dim_procedures  p ON p.procedure_id = wt.procedure_id
GROUP BY p.procedure_id, p.name, p.category, p.benchmark_90_days
ORDER BY mean_p90 DESC;


-- ── 2. Cohort analysis: COVID impact cohorts ───────────────────────────────────
--    Classify hospitals by their COVID-era performance drop,
--    then track their recovery trajectory
WITH pre_covid AS (
    SELECT
        wt.hospital_id,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS pre_covid_benchmark
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    WHERE dp.fiscal_year BETWEEN 2017 AND 2019
    GROUP BY wt.hospital_id
),
during_covid AS (
    SELECT
        wt.hospital_id,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS covid_benchmark
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    WHERE dp.is_covid_period = TRUE
    GROUP BY wt.hospital_id
),
post_covid AS (
    SELECT
        wt.hospital_id,
        ROUND(AVG(wt.pct_within_benchmark), 1) AS post_covid_benchmark
    FROM fact_wait_times wt
    JOIN dim_periods     dp ON dp.period_id = wt.period_id
    WHERE dp.is_post_covid = TRUE
    GROUP BY wt.hospital_id
),
cohorts AS (
    SELECT
        pr.hospital_id,
        pr.pre_covid_benchmark,
        dc.covid_benchmark,
        po.post_covid_benchmark,
        ROUND(dc.covid_benchmark - pr.pre_covid_benchmark, 1) AS covid_drop,
        ROUND(po.post_covid_benchmark - pr.pre_covid_benchmark, 1) AS net_recovery,
        CASE
            WHEN (po.post_covid_benchmark - pr.pre_covid_benchmark) >= 0
                THEN \'Full Recovery\'
            WHEN (po.post_covid_benchmark - pr.pre_covid_benchmark) >= -5
                THEN \'Near Recovery\'
            ELSE \'Still Lagging\'
        END AS recovery_status
    FROM pre_covid  pr
    JOIN during_covid dc USING (hospital_id)
    JOIN post_covid  po USING (hospital_id)
)
SELECT
    c.recovery_status,
    COUNT(*)                                    AS hospital_count,
    ROUND(AVG(c.pre_covid_benchmark), 1)        AS avg_pre_covid,
    ROUND(AVG(c.covid_benchmark), 1)            AS avg_during_covid,
    ROUND(AVG(c.post_covid_benchmark), 1)       AS avg_post_covid,
    ROUND(AVG(c.covid_drop), 1)                 AS avg_covid_drop_pts,
    ROUND(AVG(c.net_recovery), 1)               AS avg_net_recovery_pts,
    -- Which provinces dominate each cohort?
    STRING_AGG(DISTINCT h.province_code, \', \' ORDER BY h.province_code)
                                                AS provinces_in_cohort
FROM cohorts        c
JOIN dim_hospitals  h ON h.hospital_id = c.hospital_id
GROUP BY c.recovery_status
ORDER BY avg_post_covid DESC;


-- ── 3. Pivot-style: province performance by procedure category ─────────────────
--    Simulates a cross-tab / pivot table using conditional aggregation
SELECT
    h.province_code,
    -- One column per procedure category
    ROUND(AVG(CASE WHEN p.category = \'Orthopaedic\'   THEN wt.pct_within_benchmark END), 1)
        AS orthopaedic_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = \'Oncology\'      THEN wt.pct_within_benchmark END), 1)
        AS oncology_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = \'Cardiac\'       THEN wt.pct_within_benchmark END), 1)
        AS cardiac_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = \'Ophthalmology\' THEN wt.pct_within_benchmark END), 1)
        AS ophthalmology_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = \'Diagnostic\'    THEN wt.pct_within_benchmark END), 1)
        AS diagnostic_benchmark_pct,
    -- Overall
    ROUND(AVG(wt.pct_within_benchmark), 1) AS overall_benchmark_pct
FROM fact_wait_times wt
JOIN dim_hospitals   h ON h.hospital_id  = wt.hospital_id
JOIN dim_procedures  p ON p.procedure_id = wt.procedure_id
GROUP BY h.province_code
ORDER BY overall_benchmark_pct DESC;


-- ── 4. Urban vs Rural equity gap analysis ─────────────────────────────────────
WITH urban_rural_stats AS (
    SELECT
        h.province_code,
        h.urban_rural,
        p.name                                  AS procedure_name,
        ROUND(AVG(wt.p90_wait_days), 1)         AS avg_p90_wait,
        ROUND(AVG(wt.pct_within_benchmark), 1)  AS avg_benchmark_pct,
        SUM(wt.patient_count)                   AS total_patients
    FROM fact_wait_times wt
    JOIN dim_hospitals   h ON h.hospital_id  = wt.hospital_id
    JOIN dim_procedures  p ON p.procedure_id = wt.procedure_id
    GROUP BY h.province_code, h.urban_rural, p.name
),
equity_gap AS (
    SELECT
        u.province_code,
        u.procedure_name,
        MAX(CASE WHEN u.urban_rural = \'Urban\' THEN u.avg_p90_wait END)
            AS urban_avg_p90,
        MAX(CASE WHEN u.urban_rural = \'Rural\' THEN u.avg_p90_wait END)
            AS rural_avg_p90,
        MAX(CASE WHEN u.urban_rural = \'Rural\' THEN u.avg_p90_wait END) -
        MAX(CASE WHEN u.urban_rural = \'Urban\' THEN u.avg_p90_wait END)
            AS rural_urban_gap_days
    FROM urban_rural_stats u
    GROUP BY u.province_code, u.procedure_name
    HAVING MAX(CASE WHEN u.urban_rural = \'Urban\' THEN u.avg_p90_wait END) IS NOT NULL
       AND MAX(CASE WHEN u.urban_rural = \'Rural\' THEN u.avg_p90_wait END) IS NOT NULL
)
SELECT *
FROM equity_gap
WHERE rural_urban_gap_days > 0
ORDER BY rural_urban_gap_days DESC
LIMIT 25;
'''

with open("sql/06_advanced_analytics.sql", "w") as f:
    f.write(SQL_06)
print("✔  sql/06_advanced_analytics.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/07_views_for_bi.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_07 = '''-- ============================================================
-- 07_views_for_bi.sql
-- Creates pre-aggregated views optimised for Tableau/Power BI
-- Connect your BI tool directly to these views — not the raw tables.
-- ============================================================

-- ── View 1: Province-Year summary (for trend line + map charts) ───────────────
CREATE OR REPLACE VIEW vw_province_year_summary AS
SELECT
    h.province_code,
    h.province_name,
    dp.fiscal_year,
    dp.fiscal_year_label,
    dp.is_covid_period,
    dp.is_post_covid,
    COUNT(DISTINCT h.hospital_id)               AS reporting_hospitals,
    SUM(wt.patient_count)                       AS total_patients,
    ROUND(AVG(wt.p90_wait_days), 1)             AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1)      AS avg_benchmark_pct,
    ROUND(AVG(f.total_budget_cad / 1000000.0), 2) AS avg_budget_millions,
    SUM(f.nursing_fte)                          AS total_nursing_fte,
    SUM(f.physician_fte)                        AS total_physician_fte
FROM fact_wait_times   wt
JOIN dim_hospitals     h  ON h.hospital_id  = wt.hospital_id
JOIN dim_periods       dp ON dp.period_id   = wt.period_id
LEFT JOIN fact_financials f ON f.hospital_id = wt.hospital_id
                            AND f.period_id  = wt.period_id
GROUP BY
    h.province_code, h.province_name,
    dp.fiscal_year, dp.fiscal_year_label,
    dp.is_covid_period, dp.is_post_covid;


-- ── View 2: Hospital performance card (for scatter + ranked bar charts) ────────
CREATE OR REPLACE VIEW vw_hospital_performance_card AS
SELECT
    h.hospital_id,
    h.hospital_name,
    h.province_code,
    h.province_name,
    h.health_region,
    h.city,
    h.hospital_type,
    h.urban_rural,
    h.bed_count,
    COUNT(DISTINCT wt.procedure_id)             AS procedures_offered,
    SUM(wt.patient_count)                       AS total_patients_10yr,
    ROUND(AVG(wt.p90_wait_days), 1)             AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1)      AS avg_benchmark_pct,
    ROUND(STDDEV(wt.p90_wait_days), 1)          AS wait_time_variability,
    CASE
        WHEN AVG(wt.pct_within_benchmark) >= 90 THEN \'A — Excellent\'
        WHEN AVG(wt.pct_within_benchmark) >= 80 THEN \'B — Good\'
        WHEN AVG(wt.pct_within_benchmark) >= 70 THEN \'C — Average\'
        WHEN AVG(wt.pct_within_benchmark) >= 60 THEN \'D — Below Average\'
        ELSE                                         \'F — Critical\'
    END                                         AS performance_grade
FROM fact_wait_times wt
JOIN dim_hospitals   h ON h.hospital_id = wt.hospital_id
GROUP BY
    h.hospital_id, h.hospital_name, h.province_code, h.province_name,
    h.health_region, h.city, h.hospital_type, h.urban_rural, h.bed_count;


-- ── View 3: Procedure-level detail (for procedure deep-dive page) ──────────────
CREATE OR REPLACE VIEW vw_procedure_year_detail AS
SELECT
    p.procedure_id,
    p.name                                      AS procedure_name,
    p.category                                  AS procedure_category,
    p.benchmark_90_days,
    h.province_code,
    dp.fiscal_year_label,
    dp.is_covid_period,
    SUM(wt.patient_count)                       AS total_patients,
    ROUND(AVG(wt.p90_wait_days), 1)             AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1)      AS avg_benchmark_pct,
    ROUND(AVG(wt.p90_wait_days) / p.benchmark_90_days * 100, 1)
                                                AS pct_of_benchmark_target
FROM fact_wait_times wt
JOIN dim_hospitals   h  ON h.hospital_id  = wt.hospital_id
JOIN dim_procedures  p  ON p.procedure_id = wt.procedure_id
JOIN dim_periods     dp ON dp.period_id   = wt.period_id
GROUP BY
    p.procedure_id, p.name, p.category, p.benchmark_90_days,
    h.province_code, dp.fiscal_year_label, dp.is_covid_period;


-- ── View 4: Urban/Rural equity (for equity analysis page) ─────────────────────
CREATE OR REPLACE VIEW vw_urban_rural_equity AS
SELECT
    h.province_code,
    h.urban_rural,
    p.name                                      AS procedure_name,
    p.category,
    dp.fiscal_year_label,
    ROUND(AVG(wt.p90_wait_days), 1)             AS avg_p90_wait_days,
    ROUND(AVG(wt.pct_within_benchmark), 1)      AS avg_benchmark_pct,
    SUM(wt.patient_count)                       AS total_patients,
    COUNT(DISTINCT h.hospital_id)               AS hospital_count
FROM fact_wait_times wt
JOIN dim_hospitals   h  ON h.hospital_id  = wt.hospital_id
JOIN dim_procedures  p  ON p.procedure_id = wt.procedure_id
JOIN dim_periods     dp ON dp.period_id   = wt.period_id
GROUP BY
    h.province_code, h.urban_rural,
    p.name, p.category, dp.fiscal_year_label;


-- ── Verify views ──────────────────────────────────────────────────────────────
SELECT \'vw_province_year_summary\'      AS view_name, COUNT(*) AS rows FROM vw_province_year_summary
UNION ALL
SELECT \'vw_hospital_performance_card\',  COUNT(*) FROM vw_hospital_performance_card
UNION ALL
SELECT \'vw_procedure_year_detail\',      COUNT(*) FROM vw_procedure_year_detail
UNION ALL
SELECT \'vw_urban_rural_equity\',         COUNT(*) FROM vw_urban_rural_equity;
'''

with open("sql/07_views_for_bi.sql", "w") as f:
    f.write(SQL_07)
print("✔  sql/07_views_for_bi.sql")


# ─────────────────────────────────────────────────────────────────────────────
# sql/08_query_optimization.sql
# ─────────────────────────────────────────────────────────────────────────────
SQL_08 = '''-- ============================================================
-- 08_query_optimization.sql
-- Level: Senior DA / Junior DE
-- Concepts: EXPLAIN ANALYZE, index usage, query rewrites,
--           avoiding common performance pitfalls
-- ============================================================


-- ── CONCEPT 1: Use EXPLAIN ANALYZE to read a query plan ───────────────────────
-- Prefix any slow query with EXPLAIN (ANALYZE, BUFFERS) to see:
--   Seq Scan vs Index Scan, actual vs estimated rows, execution time
--   Run this, read the plan, then add indexes accordingly.

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    h.province_code,
    ROUND(AVG(wt.p90_wait_days), 1) AS avg_p90
FROM fact_wait_times wt
JOIN dim_hospitals   h ON h.hospital_id = wt.hospital_id
WHERE h.province_code = \'ON\'
GROUP BY h.province_code;
-- Expected: Index Scan on idx_hosp_province after first ANALYZE


-- ── CONCEPT 2: Avoid function wrapping on indexed columns ─────────────────────
-- BAD: wrapping an indexed column in a function forces a Seq Scan
SELECT *
FROM fact_wait_times
WHERE ROUND(p90_wait_days, 0) > 200;
-- The index on p90_wait_days is NOT used because of ROUND()

-- GOOD: restructure to let the index work
SELECT *
FROM fact_wait_times
WHERE p90_wait_days > 200.0;
-- This uses idx_wt_p90 directly


-- ── CONCEPT 3: EXISTS vs IN for large subqueries ──────────────────────────────
-- IN with a subquery materialises the entire subquery first — slow for large sets.
-- EXISTS stops as soon as it finds the first match — often much faster.

-- Slower pattern with IN:
SELECT hospital_name
FROM dim_hospitals h
WHERE h.hospital_id IN (
    SELECT hospital_id
    FROM fact_wait_times
    WHERE p90_wait_days > 300
);

-- Faster pattern with EXISTS:
SELECT hospital_name
FROM dim_hospitals h
WHERE EXISTS (
    SELECT 1
    FROM fact_wait_times wt
    WHERE wt.hospital_id = h.hospital_id
      AND wt.p90_wait_days > 300
);


-- ── CONCEPT 4: Pre-filtering with CTEs vs derived tables ──────────────────────
-- Push filters as early as possible in the query — before joining, not after.

-- Less efficient: join everything, then filter
SELECT h.hospital_name, AVG(wt.p90_wait_days)
FROM fact_wait_times   wt
JOIN dim_hospitals     h  ON h.hospital_id  = wt.hospital_id
JOIN dim_periods       dp ON dp.period_id   = wt.period_id
WHERE dp.fiscal_year >= 2020
  AND h.province_code IN (\'ON\',\'QC\',\'BC\')
  AND wt.p90_wait_days > 100
GROUP BY h.hospital_name;

-- More efficient: filter in CTE before joining
WITH filtered_wt AS (
    SELECT hospital_id, period_id, p90_wait_days
    FROM fact_wait_times
    WHERE p90_wait_days > 100          -- filter fact table FIRST
),
recent_periods AS (
    SELECT period_id
    FROM dim_periods
    WHERE fiscal_year >= 2020          -- filter dimension FIRST
),
target_hospitals AS (
    SELECT hospital_id, hospital_name
    FROM dim_hospitals
    WHERE province_code IN (\'ON\',\'QC\',\'BC\')  -- filter dimension FIRST
)
SELECT h.hospital_name, ROUND(AVG(f.p90_wait_days), 1) AS avg_p90
FROM filtered_wt     f
JOIN recent_periods  rp ON rp.period_id  = f.period_id
JOIN target_hospitals h ON h.hospital_id = f.hospital_id
GROUP BY h.hospital_name
ORDER BY avg_p90 DESC;


-- ── CONCEPT 5: Partial indexes for filtered queries ───────────────────────────
-- If you frequently query for a specific subset, a partial index is smaller
-- and faster than a full index.

-- Create a partial index only for COVID-period records (often queried)
CREATE INDEX IF NOT EXISTS idx_wt_covid_p90
ON fact_wait_times (p90_wait_days)
WHERE period_id IN (SELECT period_id FROM dim_periods WHERE is_covid_period = TRUE);

-- Create a partial index for rural hospitals specifically
CREATE INDEX IF NOT EXISTS idx_wt_rural_hospitals
ON fact_wait_times (hospital_id, p90_wait_days)
WHERE hospital_id IN (
    SELECT hospital_id FROM dim_hospitals WHERE urban_rural = \'Rural\'
);


-- ── CONCEPT 6: Analyse table statistics ───────────────────────────────────────
-- After loading large amounts of data, ANALYZE updates the query planner\'s
-- statistics so it makes better decisions about index usage.

ANALYZE fact_wait_times;
ANALYZE dim_hospitals;

-- Check current table sizes and index usage
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||\'.\' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||\'.\' || tablename))       AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||\'.\' || tablename)
                 - pg_relation_size(schemaname||\'.\' || tablename))       AS index_size
FROM pg_tables
WHERE schemaname = \'public\'
ORDER BY pg_total_relation_size(schemaname||\'.\' || tablename) DESC;
'''

with open("sql/08_query_optimization.sql", "w") as f:
    f.write(SQL_08)
print("✔  sql/08_query_optimization.sql")


# ─────────────────────────────────────────────────────────────────────────────
# src/eda.py
# ─────────────────────────────────────────────────────────────────────────────
EDA = '''"""
src/eda.py
==========
Exploratory Data Analysis — generates all charts for the portfolio.
Saves publication-quality figures to figures/ directory.

Run: python src/eda.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

os.makedirs("figures", exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#fafafa",
    "axes.facecolor":   "#fafafa",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.color":       "#cccccc",
    "font.family":      "DejaVu Sans",
    "font.size":        10,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.labelsize":   10,
})

NAVY  = "#0d1b2a"
GOLD  = "#e8b86d"
TEAL  = "#2196a6"
RED   = "#e06c75"
GREEN = "#52c987"
GRAY  = "#8a99a8"

PROVINCE_COLORS = {
    "ON": "#e8b86d", "QC": "#e06c75", "BC": "#52c987", "AB": "#2196a6",
    "MB": "#9c59d1", "SK": "#ff7043", "NS": "#26a69a", "NB": "#ec407a",
    "NL": "#7e57c2", "PE": "#29b6f6",
}

def load_data():
    hospitals  = pd.read_csv("data/dim_hospitals.csv")
    procedures = pd.read_csv("data/dim_procedures.csv")
    periods    = pd.read_csv("data/dim_periods.csv")
    wt         = pd.read_csv("data/fact_wait_times.csv")
    fin        = pd.read_csv("data/fact_financials.csv")
    return hospitals, procedures, periods, wt, fin

def fig1_national_trend(wt, periods):
    """National wait time trend 2014-2023 with COVID annotation."""
    df = (wt.merge(periods, on="period_id")
            .groupby(["fiscal_year", "fiscal_year_label", "is_covid_period"])
            .agg(avg_p90=("p90_wait_days","mean"),
                 avg_bench=("pct_within_benchmark","mean"),
                 total_patients=("patient_count","sum"))
            .reset_index())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Canadian Hospital Wait Times — National Trend (2014–2023)",
                 fontsize=15, fontweight="bold", color=NAVY, y=1.02)

    # Left: P90 wait time
    ax = axes[0]
    colors = [RED if c else TEAL for c in df["is_covid_period"]]
    ax.bar(df["fiscal_year_label"], df["avg_p90"], color=colors, alpha=0.85, width=0.7)
    ax.axhspan(df["avg_p90"].min() - 5, df["avg_p90"].max() + 5,
               where=[c for c in df["is_covid_period"]], alpha=0, color="none")
    # COVID annotation
    covid_years = df[df["is_covid_period"]]
    if len(covid_years):
        ax.axvspan(
            covid_years["fiscal_year_label"].iloc[0],
            covid_years["fiscal_year_label"].iloc[-1],
            alpha=0.12, color=RED, label="COVID Period"
        )
    ax.set_title("Avg 90th Percentile Wait Time (Days)")
    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Days")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    # Right: Benchmark compliance
    ax2 = axes[1]
    ax2.plot(df["fiscal_year_label"], df["avg_bench"],
             color=TEAL, linewidth=2.5, marker="o", markersize=6, label="Benchmark %")
    ax2.fill_between(df["fiscal_year_label"], df["avg_bench"],
                     alpha=0.15, color=TEAL)
    ax2.axhline(90, color=GREEN, linestyle="--", linewidth=1.5, label="90% target")
    covid_idx = df[df["is_covid_period"]].index.tolist()
    for idx in covid_idx:
        ax2.axvline(df.loc[idx, "fiscal_year_label"],
                    color=RED, alpha=0.3, linewidth=8)
    ax2.set_title("Avg % Patients Within Benchmark")
    ax2.set_xlabel("Fiscal Year")
    ax2.set_ylabel("% Within Benchmark")
    ax2.tick_params(axis="x", rotation=45)
    ax2.set_ylim(50, 105)
    ax2.legend()

    plt.tight_layout()
    plt.savefig("figures/01_national_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/01_national_trend.png")

def fig2_province_heatmap(wt, hospitals, periods):
    """Province × Fiscal Year heatmap of benchmark compliance."""
    df = (wt.merge(hospitals[["hospital_id","province_code"]], on="hospital_id")
            .merge(periods[["period_id","fiscal_year_label"]], on="period_id")
            .groupby(["province_code","fiscal_year_label"])
            ["pct_within_benchmark"].mean()
            .reset_index())

    pivot = df.pivot(index="province_code", columns="fiscal_year_label",
                     values="pct_within_benchmark")

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=55, vmax=100)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Province × Year Benchmark Compliance Heatmap (%)",
                 fontsize=14, fontweight="bold", pad=15)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}",
                        ha="center", va="center",
                        fontsize=8,
                        color="white" if val < 72 else "black")

    plt.colorbar(im, ax=ax, label="% Within Benchmark", fraction=0.03)
    plt.tight_layout()
    plt.savefig("figures/02_province_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/02_province_heatmap.png")

def fig3_procedure_boxplot(wt, procedures):
    """Box plot of P90 wait time distribution per procedure."""
    df = wt.merge(procedures[["procedure_id","name","benchmark_90_days"]],
                  on="procedure_id")

    order = (df.groupby("name")["p90_wait_days"].median()
               .sort_values(ascending=False).index)

    fig, ax = plt.subplots(figsize=(14, 6))
    bp_data = [df[df["name"] == proc]["p90_wait_days"].dropna().values
               for proc in order]
    bp = ax.boxplot(bp_data, vert=True, patch_artist=True,
                    medianprops=dict(color=NAVY, linewidth=2),
                    flierprops=dict(marker=".", markersize=2, alpha=0.3))

    palette = [TEAL, GOLD, GREEN, RED, "#9c59d1", "#ff7043", "#26a69a", "#ec407a"]
    for patch, color in zip(bp["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    # Benchmark line per procedure
    benchmarks = {row["name"]: row["benchmark_90_days"]
                  for _, row in procedures.iterrows()}
    for i, proc in enumerate(order):
        bench = benchmarks.get(proc, None)
        if bench:
            ax.plot([i + 0.6, i + 1.4], [bench, bench],
                    color=RED, linewidth=1.5, linestyle="--", alpha=0.8)

    ax.set_xticklabels(order, rotation=30, ha="right")
    ax.set_ylabel("90th Percentile Wait (Days)")
    ax.set_title("P90 Wait Time Distribution by Procedure\n(dashed red = CIHI benchmark)",
                 fontsize=13, fontweight="bold")

    bench_line = mpatches.Patch(color=RED, label="CIHI Benchmark Target", linestyle="--")
    ax.legend(handles=[bench_line], loc="upper right")
    plt.tight_layout()
    plt.savefig("figures/03_procedure_boxplot.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/03_procedure_boxplot.png")

def fig4_urban_rural_equity(wt, hospitals, procedures):
    """Urban vs Rural wait time gap by procedure."""
    df = (wt.merge(hospitals[["hospital_id","urban_rural"]], on="hospital_id")
            .merge(procedures[["procedure_id","name"]], on="procedure_id")
            .groupby(["urban_rural","name"])["p90_wait_days"]
            .mean().reset_index())

    urban  = df[df["urban_rural"] == "Urban"].set_index("name")["p90_wait_days"]
    rural  = df[df["urban_rural"] == "Rural"].set_index("name")["p90_wait_days"]
    procs  = urban.index.intersection(rural.index)
    gap    = (rural[procs] - urban[procs]).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [GREEN if g < 0 else RED for g in gap.values]
    ax.barh(gap.index, gap.values, color=colors, alpha=0.8)
    ax.axvline(0, color=NAVY, linewidth=1.2)
    ax.set_xlabel("Rural − Urban Wait Days (Equity Gap)")
    ax.set_title("Urban–Rural Wait Time Equity Gap by Procedure\n(positive = Rural waits longer)",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(gap.min() - 10, gap.max() + 20)

    for i, (val, idx) in enumerate(zip(gap.values, gap.index)):
        ax.text(val + 1.5, i, f"+{val:.0f}d" if val >= 0 else f"{val:.0f}d",
                va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig("figures/04_urban_rural_equity.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/04_urban_rural_equity.png")

def fig5_volume_vs_performance(wt, hospitals):
    """Scatter: hospital volume vs benchmark performance (coloured by type)."""
    df = (wt.merge(hospitals[["hospital_id","hospital_type","province_code",
                               "urban_rural","bed_count"]], on="hospital_id")
            .groupby(["hospital_id","hospital_type","province_code",
                      "urban_rural","bed_count"])
            .agg(total_patients=("patient_count","sum"),
                 avg_benchmark=("pct_within_benchmark","mean"))
            .reset_index())

    type_colors = {"Teaching": TEAL, "Community": GOLD,
                   "Rural": RED, "Specialty": GREEN}
    fig, ax = plt.subplots(figsize=(11, 7))

    for htype, group in df.groupby("hospital_type"):
        ax.scatter(group["total_patients"], group["avg_benchmark"],
                   color=type_colors.get(htype, GRAY),
                   alpha=0.6, s=group["bed_count"] / 5,
                   label=htype, edgecolors="white", linewidths=0.4)

    ax.axhline(90, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7,
               label="90% benchmark target")
    ax.set_xlabel("Total Patients Treated (10-year sum)")
    ax.set_ylabel("Avg % Patients Within Benchmark")
    ax.set_title("Hospital Volume vs Performance\n(bubble size = bed count)",
                 fontsize=13, fontweight="bold")
    ax.legend(title="Hospital Type", loc="lower right")
    plt.tight_layout()
    plt.savefig("figures/05_volume_vs_performance.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/05_volume_vs_performance.png")

def main():
    print("Loading data …")
    hospitals, procedures, periods, wt, fin = load_data()
    print(f"  {len(wt):,} wait time records loaded")

    print("\\nGenerating figures …")
    fig1_national_trend(wt, periods)
    fig2_province_heatmap(wt, hospitals, periods)
    fig3_procedure_boxplot(wt, procedures)
    fig4_urban_rural_equity(wt, hospitals, procedures)
    fig5_volume_vs_performance(wt, hospitals)

    print(f"\\n✔  All figures saved to figures/")

if __name__ == "__main__":
    main()
'''

with open("src/eda.py", "w") as f:
    f.write(EDA)
print("✔  src/eda.py")


# ─────────────────────────────────────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────────────────────────────────────
REQUIREMENTS = """\
# Data
numpy==1.26.4
pandas==2.2.1
scipy==1.12.0

# Visualisation
matplotlib==3.8.3
seaborn==0.13.2

# PostgreSQL
psycopg2-binary==2.9.9
sqlalchemy==2.0.28

# Notebook
jupyterlab==4.1.5
ipykernel==6.29.3
"""

with open("requirements.txt", "w") as f:
    f.write(REQUIREMENTS)
print("✔  requirements.txt")


# ─────────────────────────────────────────────────────────────────────────────
# dashboard/README_dashboard.md
# ─────────────────────────────────────────────────────────────────────────────
DASHBOARD_README = """\
# Dashboard Build Instructions

## Connect to PostgreSQL Views

Both Tableau and Power BI connect directly to the 4 views
created in `sql/07_views_for_bi.sql`.

### Tableau
1. Connect → PostgreSQL
2. Server: localhost | Port: 5432 | Database: canhealth
3. Tables to use (under the public schema):
   - vw_province_year_summary
   - vw_hospital_performance_card
   - vw_procedure_year_detail
   - vw_urban_rural_equity

### Power BI
1. Get Data → PostgreSQL database
2. Server: localhost:5432 | Database: canhealth
3. Select the same 4 views above
4. Load (not Transform — the views are already clean)

## Dashboard Pages to Build

### Page 1 — Executive Overview (KPI Cards + Trend)
- KPI cards: Avg P90 wait, % within benchmark, total patients, hospitals reporting
- Line chart: national benchmark % trend 2014–2023 (annotate COVID)
- Bar chart: top 5 and bottom 5 provinces by benchmark compliance

### Page 2 — Province Deep Dive (Map + Filters)
- Canadian province map coloured by avg benchmark %
- Slicer: fiscal year, procedure category
- Table: province ranking with YoY change arrows

### Page 3 — Procedure Analysis
- Clustered bar: avg P90 vs benchmark target per procedure
- Scatter: volume (x) vs benchmark % (y), coloured by procedure

### Page 4 — Equity Analysis
- Side-by-side bar: urban vs rural wait times per procedure
- Equity gap heatmap: province × urban/rural

### Page 5 — Hospital Scorecard
- Searchable table with performance grade, volume, wait time
- Scatter: bed count vs avg wait time
"""

with open("dashboard/README_dashboard.md", "w") as f:
    f.write(DASHBOARD_README)
print("✔  dashboard/README_dashboard.md")


# ─────────────────────────────────────────────────────────────────────────────
# README.md
# ─────────────────────────────────────────────────────────────────────────────
README = """\
# CanHealth Analytics
## Senior Data Analyst Portfolio Project

**Domain:** Canadian Healthcare — CIHI Wait Times for Priority Procedures

---

## Architecture

```
canhealth-analytics/
├── src/
│   ├── generate_data.py   ← Synthetic CIHI-modelled data generation
│   ├── load_postgres.py   ← Loads CSVs into PostgreSQL star schema
│   └── eda.py             ← EDA + 5 publication-quality figures
├── sql/
│   ├── 01_schema.sql      ← Star schema DDL + indexes
│   ├── 02_basic_exploration.sql
│   ├── 03_joins_aggregations.sql
│   ├── 04_ctes_subqueries.sql
│   ├── 05_window_functions.sql
│   ├── 06_advanced_analytics.sql
│   ├── 07_views_for_bi.sql  ← Views for Tableau / Power BI
│   └── 08_query_optimization.sql
├── data/         ← Generated CSVs (star schema)
├── figures/      ← Output charts from eda.py
└── dashboard/    ← BI tool connection instructions
```

## Quick Start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/generate_data.py
python src/eda.py
# Optional — requires PostgreSQL running:
python src/load_postgres.py
```
"""

with open("README.md", "w") as f:
    f.write(README)
print("✔  README.md")

# ─────────────────────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════════════╗
║        CanHealth Analytics — scaffold complete                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1.  pip install -r requirements.txt                             ║
║  2.  python src/generate_data.py     → 5 CSVs in data/           ║
║  3.  python src/eda.py               → 5 figures in figures/     ║
║  4.  (PostgreSQL) python src/load_postgres.py                    ║
║  5.  Run SQL files in order: 01 → 08                             ║
║  6.  Connect Tableau/Power BI to the views in 07_views_for_bi    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
