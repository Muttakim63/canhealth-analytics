-- ============================================================
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
        WHEN AVG(wt.pct_within_benchmark) >= 90 THEN 'A — Excellent'
        WHEN AVG(wt.pct_within_benchmark) >= 80 THEN 'B — Good'
        WHEN AVG(wt.pct_within_benchmark) >= 70 THEN 'C — Average'
        WHEN AVG(wt.pct_within_benchmark) >= 60 THEN 'D — Below Average'
        ELSE                                         'F — Critical'
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
SELECT 'vw_province_year_summary'      AS view_name, COUNT(*) AS rows FROM vw_province_year_summary
UNION ALL
SELECT 'vw_hospital_performance_card',  COUNT(*) FROM vw_hospital_performance_card
UNION ALL
SELECT 'vw_procedure_year_detail',      COUNT(*) FROM vw_procedure_year_detail
UNION ALL
SELECT 'vw_urban_rural_equity',         COUNT(*) FROM vw_urban_rural_equity;
