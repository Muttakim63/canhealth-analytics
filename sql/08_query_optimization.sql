-- ============================================================
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
WHERE h.province_code = 'ON'
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
  AND h.province_code IN ('ON','QC','BC')
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
    WHERE province_code IN ('ON','QC','BC')  -- filter dimension FIRST
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
    SELECT hospital_id FROM dim_hospitals WHERE urban_rural = 'Rural'
);


-- ── CONCEPT 6: Analyse table statistics ───────────────────────────────────────
-- After loading large amounts of data, ANALYZE updates the query planner's
-- statistics so it makes better decisions about index usage.

ANALYZE fact_wait_times;
ANALYZE dim_hospitals;

-- Check current table sizes and index usage
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.' || tablename))       AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.' || tablename)
                 - pg_relation_size(schemaname||'.' || tablename))       AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.' || tablename) DESC;
