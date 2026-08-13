-- ============================================================
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
        WHEN dp.is_covid_period THEN 'During COVID (2020-21)'
        WHEN dp.is_post_covid   THEN 'Post-COVID (2022-23)'
        ELSE                         'Pre-COVID (2014-19)'
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
