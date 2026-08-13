-- ============================================================
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
                THEN 'Full Recovery'
            WHEN (po.post_covid_benchmark - pr.pre_covid_benchmark) >= -5
                THEN 'Near Recovery'
            ELSE 'Still Lagging'
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
    STRING_AGG(DISTINCT h.province_code, ', ' ORDER BY h.province_code)
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
    ROUND(AVG(CASE WHEN p.category = 'Orthopaedic'   THEN wt.pct_within_benchmark END), 1)
        AS orthopaedic_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = 'Oncology'      THEN wt.pct_within_benchmark END), 1)
        AS oncology_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = 'Cardiac'       THEN wt.pct_within_benchmark END), 1)
        AS cardiac_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = 'Ophthalmology' THEN wt.pct_within_benchmark END), 1)
        AS ophthalmology_benchmark_pct,
    ROUND(AVG(CASE WHEN p.category = 'Diagnostic'    THEN wt.pct_within_benchmark END), 1)
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
        MAX(CASE WHEN u.urban_rural = 'Urban' THEN u.avg_p90_wait END)
            AS urban_avg_p90,
        MAX(CASE WHEN u.urban_rural = 'Rural' THEN u.avg_p90_wait END)
            AS rural_avg_p90,
        MAX(CASE WHEN u.urban_rural = 'Rural' THEN u.avg_p90_wait END) -
        MAX(CASE WHEN u.urban_rural = 'Urban' THEN u.avg_p90_wait END)
            AS rural_urban_gap_days
    FROM urban_rural_stats u
    GROUP BY u.province_code, u.procedure_name
    HAVING MAX(CASE WHEN u.urban_rural = 'Urban' THEN u.avg_p90_wait END) IS NOT NULL
       AND MAX(CASE WHEN u.urban_rural = 'Rural' THEN u.avg_p90_wait END) IS NOT NULL
)
SELECT *
FROM equity_gap
WHERE rural_urban_gap_days > 0
ORDER BY rural_urban_gap_days DESC
LIMIT 25;
