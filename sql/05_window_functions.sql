-- ============================================================
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
    WHERE p.code = 'HIP_REP'
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
        THEN 'High Priority — High Volume, Low Performance'
        WHEN NTILE(4) OVER (ORDER BY total_patients)         = 4
         AND NTILE(4) OVER (ORDER BY avg_benchmark_pct DESC) = 4
        THEN 'Model Hospital — High Volume, High Performance'
        ELSE 'Standard'
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
