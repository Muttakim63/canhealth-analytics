# 🏥 CanHealth Analytics — Healthcare Data Warehouse & Analytics Engine

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQL Architecture](https://img.shields.io/badge/SQL-Star_Schema-blue?style=for-the-badge)](https://en.wikipedia.org/wiki/Star_schema)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An enterprise-grade **Healthcare Data Warehouse & Analytics Platform** built to analyze hospital operational efficiency, wait time benchmark compliance, financial sustainability, and healthcare access equity across Canadian health systems.

---

## 🖥️ Interactive Dashboard Preview

![CanHealth Analytics Dashboard Preview](assets/dashboard_preview.png)

---

## 📌 Project Overview & Business Value

Healthcare leadership across Canada faces a complex dual challenge: **reducing procedure wait times** while **managing escalating hospital operating costs**. 

`canhealth-analytics` models a multi-subject **Star Schema Data Warehouse** that unifies clinical wait times (90th percentile wait in days, benchmark compliance percentages) with hospital financial statements (operating budget, actual spend, nursing & physician staffing FTEs).

---

## 🏗️ Data Warehouse Star Schema Architecture

```mermaid
erDiagram
    DIM_HOSPITALS ||--o{ FACT_WAIT_TIMES : "operates"
    DIM_PERIODS ||--o{ FACT_WAIT_TIMES : "recorded_in"
    DIM_PROCEDURES ||--o{ FACT_WAIT_TIMES : "measures"
    DIM_HOSPITALS ||--o{ FACT_FINANCIALS : "reports"
    DIM_PERIODS ||--o{ FACT_FINANCIALS : "fiscal_year"

    DIM_HOSPITALS {
        int hospital_id PK
        string hospital_name
        string province_name
        string health_region
        string hospital_type
        string urban_rural
        int bed_count
    }

    DIM_PROCEDURES {
        int procedure_id PK
        string code
        string name
        string category
        int benchmark_90_days
    }

    DIM_PERIODS {
        int period_id PK
        int fiscal_year
        int quarter
        string period_name
    }

    FACT_WAIT_TIMES {
        int record_id PK
        int hospital_id FK
        int period_id FK
        int procedure_id FK
        int patient_count
        float p50_wait_days
        float p90_wait_days
        float pct_within_benchmark
    }

    FACT_FINANCIALS {
        int hospital_id FK
        int period_id FK
        int fiscal_year
        float total_budget_cad
        float actual_spend_cad
        int nursing_fte
        int physician_fte
    }
```

---

## 💻 SQL Mastery & Analytics Engineering Highlights

The repository contains 8 production SQL scripts in `sql/` demonstrating advanced analytics engineering:

1. **`01_schema.sql`**: Data Definition Language (DDL) for dimensional tables, primary keys, foreign keys, and check constraints.
2. **`02_basic_exploration.sql`**: Data profiling, row counting, and data completeness auditing.
3. **`03_joins_aggregations.sql`**: Multi-fact table aggregations joining clinical wait times with financial metrics.
4. **`04_ctes_subqueries.sql`**: Multi-step Common Table Expressions (CTEs) for complex cohort analysis.
5. **`05_window_functions.sql`**: Advanced analytic windowing (`RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `NTILE()`, running totals).
6. **`06_advanced_analytics.sql`**: Year-over-Year (YoY) growth calculations, hospital efficiency scoring, and outlier detection.
7. **`07_views_for_bi.sql`**: Materialized & Business Intelligence views optimized for Tableau, PowerBI, and Streamlit.
8. **`08_query_optimization.sql`**: B-Tree composite indexes, `EXPLAIN ANALYZE` execution plan tuning, and query optimization.

---

## 🖥️ Interactive Streamlit BI Analytics Dashboard

The platform includes a 5-page interactive Business Intelligence portal (`dashboard/streamlit_dashboard.py`):

1. **📊 Executive Overview**: National KPI metric cards, 10-year benchmark compliance trend lines, and provincial rank charts.
2. **🗺️ Province Deep Dive**: Interactive provincial comparison filtered by procedure category and fiscal year.
3. **🩺 Procedure Analysis**: Actual 90th percentile wait times vs National Benchmark targets per procedure type.
4. **⚖️ Equity Analysis**: Side-by-side wait time comparisons between Urban vs Rural healthcare facilities.
5. **🏥 Hospital Scorecard**: Searchable operational performance table showing bed capacity, patient volume, and wait times.

---

## 🚀 Quick Start & Running Locally

### 1. Clone the Repository
```bash
git clone https://github.com/Muttakim63/canhealth-analytics.git
cd canhealth-analytics
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate Local Database (SQLite / PostgreSQL Compatible)
```bash
python setup_sqlite.py
```

### 4. Launch the Interactive BI Analytics Dashboard
```bash
streamlit run dashboard/streamlit_dashboard.py
```

---

## 📂 Repository Structure

```
canhealth-analytics/
├── assets/
│   └── dashboard_preview.png     # Interactive BI dashboard preview screenshot
├── dashboard/
│   ├── streamlit_dashboard.py    # 5-page Streamlit BI dashboard portal
│   └── README_dashboard.md       # BI connect instructions for Tableau/PowerBI
├── data/
│   ├── dim_hospitals.csv         # Hospital dimension table
│   ├── dim_periods.csv           # Fiscal period dimension table
│   ├── dim_procedures.csv        # Procedure benchmark dimension table
│   ├── fact_financials.csv       # Hospital financial performance fact table
│   └── fact_wait_times.csv       # Clinical wait times fact table
├── sql/
│   ├── 01_schema.sql             # DDL Star Schema definition
│   ├── 02_basic_exploration.sql  # Data auditing queries
│   ├── 03_joins_aggregations.sql # Multi-fact table aggregations
│   ├── 04_ctes_subqueries.sql    # Complex CTE queries
│   ├── 05_window_functions.sql   # Window functions (LAG, RANK, NTILE)
│   ├── 06_advanced_analytics.sql # YoY growth & hospital efficiency scoring
│   ├── 07_views_for_bi.sql       # Views for BI dashboards
│   └── 08_query_optimization.sql # B-Tree indexes & EXPLAIN ANALYZE tuning
├── src/
│   ├── eda.py                    # Exploratory Data Analysis python script
│   ├── generate_data.py          # Data warehouse synthesizer
│   └── load_postgres.py          # Postgres bulk loader script
├── setup_sqlite.py               # Self-contained database generator
├── requirements.txt              # Project dependencies
└── README.md                     # Documentation & architecture ERD
```

---

## 👨‍💻 Author

Developed by **Muttakim_A** ([@Muttakim63](https://github.com/Muttakim63))  
*Building Data Warehouses and Analytics Engineering Solutions for Healthcare.*
