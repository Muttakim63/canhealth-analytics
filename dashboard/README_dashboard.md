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
