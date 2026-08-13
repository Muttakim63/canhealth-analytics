-- ============================================================
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
                THEN 'Top Performer'
            WHEN pa.avg_benchmark_pct >= nb.national_avg_benchmark_pct - 2
                THEN 'On Par'
            WHEN pa.avg_benchmark_pct >= nb.national_avg_benchmark_pct - 10
                THEN 'Below Average'
            ELSE 'Needs Attention'
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
        WHEN i.benchmark_pct_gained >= 15 THEN 'Major Improvement'
        WHEN i.benchmark_pct_gained >= 5  THEN 'Moderate Improvement'
        WHEN i.benchmark_pct_gained >= 0  THEN 'Stable'
        ELSE 'Declined'
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
        WHERE wt.hospital_id = h.hospital_id AND p.code = 'HIP_REP'
    )
    AND EXISTS (
        SELECT 1 FROM fact_wait_times wt
        JOIN dim_procedures p ON p.procedure_id = wt.procedure_id
        WHERE wt.hospital_id = h.hospital_id AND p.code = 'KNEE_REP'
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
