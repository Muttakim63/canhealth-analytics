-- ============================================================
-- 01_schema.sql
-- CanHealth Analytics — Database Schema
-- Star schema: 3 dimension tables + 2 fact tables
-- ============================================================

-- Drop in reverse dependency order
DROP TABLE IF EXISTS fact_financials    CASCADE;
DROP TABLE IF EXISTS fact_wait_times    CASCADE;
DROP TABLE IF EXISTS dim_hospitals      CASCADE;
DROP TABLE IF EXISTS dim_procedures     CASCADE;
DROP TABLE IF EXISTS dim_periods        CASCADE;

-- ── Dimension: Fiscal Periods ────────────────────────────────────────────────
CREATE TABLE dim_periods (
    period_id           SERIAL PRIMARY KEY,
    fiscal_year         SMALLINT    NOT NULL,
    fiscal_year_label   VARCHAR(10) NOT NULL,   -- e.g. "2019-20"
    is_covid_period     BOOLEAN     NOT NULL DEFAULT FALSE,
    is_post_covid       BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_period UNIQUE (fiscal_year)
);

-- ── Dimension: Procedures ────────────────────────────────────────────────────
CREATE TABLE dim_procedures (
    procedure_id        SERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,
    name                VARCHAR(80) NOT NULL,
    category            VARCHAR(40) NOT NULL,
    benchmark_50_days   SMALLINT    NOT NULL,
    benchmark_90_days   SMALLINT    NOT NULL,
    complexity          VARCHAR(10) NOT NULL CHECK (complexity IN ('low','high','urgent')),
    requires_specialist BOOLEAN     NOT NULL DEFAULT TRUE
);

-- ── Dimension: Hospitals ─────────────────────────────────────────────────────
CREATE TABLE dim_hospitals (
    hospital_id         SERIAL PRIMARY KEY,
    hospital_name       VARCHAR(120) NOT NULL,
    province_code       CHAR(2)      NOT NULL,
    province_name       VARCHAR(40)  NOT NULL,
    health_region       VARCHAR(60)  NOT NULL,
    city                VARCHAR(60)  NOT NULL,
    hospital_type       VARCHAR(20)  NOT NULL
        CHECK (hospital_type IN ('Teaching','Community','Rural','Specialty')),
    urban_rural         VARCHAR(10)  NOT NULL CHECK (urban_rural IN ('Urban','Rural')),
    bed_count           SMALLINT     NOT NULL CHECK (bed_count > 0),
    established_year    SMALLINT
);

-- ── Fact: Wait Times ─────────────────────────────────────────────────────────
CREATE TABLE fact_wait_times (
    record_id               BIGSERIAL   PRIMARY KEY,
    hospital_id             INT         NOT NULL REFERENCES dim_hospitals(hospital_id),
    procedure_id            INT         NOT NULL REFERENCES dim_procedures(procedure_id),
    period_id               INT         NOT NULL REFERENCES dim_periods(period_id),
    patient_count           INT         NOT NULL CHECK (patient_count >= 0),
    p50_wait_days           NUMERIC(7,1),
    p90_wait_days           NUMERIC(7,1),
    pct_within_benchmark    NUMERIC(5,1) CHECK (pct_within_benchmark BETWEEN 0 AND 100),
    data_completeness       VARCHAR(10)  DEFAULT 'Complete'
);

-- ── Fact: Financials ─────────────────────────────────────────────────────────
CREATE TABLE fact_financials (
    hospital_id         INT         NOT NULL REFERENCES dim_hospitals(hospital_id),
    period_id           INT         NOT NULL REFERENCES dim_periods(period_id),
    fiscal_year         SMALLINT    NOT NULL,
    total_budget_cad    BIGINT,
    actual_spend_cad    BIGINT,
    nursing_fte         SMALLINT,
    physician_fte       SMALLINT,
    admin_fte           SMALLINT,
    or_rooms            SMALLINT,
    PRIMARY KEY (hospital_id, period_id)
);

-- ── Indexes for query performance ─────────────────────────────────────────────
-- High-cardinality foreign keys on the fact tables
CREATE INDEX idx_wt_hospital    ON fact_wait_times (hospital_id);
CREATE INDEX idx_wt_procedure   ON fact_wait_times (procedure_id);
CREATE INDEX idx_wt_period      ON fact_wait_times (period_id);
CREATE INDEX idx_wt_pct_bench   ON fact_wait_times (pct_within_benchmark);
CREATE INDEX idx_wt_p90         ON fact_wait_times (p90_wait_days);
CREATE INDEX idx_fin_hospital   ON fact_financials (hospital_id);
CREATE INDEX idx_fin_period     ON fact_financials (period_id);

-- Composite index for the most common analytical join pattern
CREATE INDEX idx_wt_hosp_proc_period ON fact_wait_times (hospital_id, procedure_id, period_id);

-- Province filtering is very common in healthcare analytics
CREATE INDEX idx_hosp_province  ON dim_hospitals (province_code);
CREATE INDEX idx_hosp_type      ON dim_hospitals (hospital_type);

-- ── Comments (good practice for team environments) ────────────────────────────
COMMENT ON TABLE fact_wait_times IS
    'Primary fact table. One row per hospital-procedure-year combination. '
    'Modelled after CIHI Wait Times for Priority Procedures dataset.';

COMMENT ON COLUMN fact_wait_times.p90_wait_days IS
    '90th percentile wait time in days. CIHI benchmark is measured at this percentile.';

COMMENT ON COLUMN fact_wait_times.pct_within_benchmark IS
    'Percentage of patients who received care within the CIHI benchmark target.';
