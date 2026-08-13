-- ============================================================
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
        WHEN wt.pct_within_benchmark >= 90 THEN 'Met'
        WHEN wt.pct_within_benchmark >= 70 THEN 'Near-Miss'
        ELSE                                    'Missed'
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
        WHEN AVG(wt.pct_within_benchmark) >= 90 THEN 'A'
        WHEN AVG(wt.pct_within_benchmark) >= 80 THEN 'B'
        WHEN AVG(wt.pct_within_benchmark) >= 70 THEN 'C'
        WHEN AVG(wt.pct_within_benchmark) >= 60 THEN 'D'
        ELSE                                          'F'
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
        WHEN COUNT(f.hospital_id) = 0 THEN 'No financial data'
        WHEN COUNT(f.hospital_id) < 5 THEN 'Partial data'
        ELSE 'Complete'
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
        WHEN f.actual_spend_cad > f.total_budget_cad THEN 'Over Budget'
        ELSE 'Within Budget'
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
