# CanHealth Analytics

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
