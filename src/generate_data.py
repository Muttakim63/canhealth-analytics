"""
src/generate_data.py
====================
Generates a synthetic but realistic CIHI-modelled dataset with:
  - 150 Canadian hospitals across 13 provinces/territories
  - 8 priority procedures (matching real CIHI benchmarks)
  - 10 fiscal years (2014-15 through 2023-24)
  - ~180,000 wait time records in a star schema
  - Hospital financials and staffing data

Run: python src/generate_data.py
"""

import numpy as np
import pandas as pd
import os

RNG = np.random.default_rng(seed=2024)

# ── Dimension: Provinces ──────────────────────────────────────────────────────
PROVINCES = {
    "ON": {"name": "Ontario",               "weight": 0.38, "urban_rate": 0.87},
    "QC": {"name": "Quebec",                "weight": 0.23, "urban_rate": 0.81},
    "BC": {"name": "British Columbia",      "weight": 0.13, "urban_rate": 0.87},
    "AB": {"name": "Alberta",               "weight": 0.11, "urban_rate": 0.83},
    "MB": {"name": "Manitoba",              "weight": 0.04, "urban_rate": 0.72},
    "SK": {"name": "Saskatchewan",          "weight": 0.03, "urban_rate": 0.66},
    "NS": {"name": "Nova Scotia",           "weight": 0.03, "urban_rate": 0.55},
    "NB": {"name": "New Brunswick",         "weight": 0.02, "urban_rate": 0.56},
    "NL": {"name": "Newfoundland",          "weight": 0.01, "urban_rate": 0.60},
    "PE": {"name": "Prince Edward Island",  "weight": 0.004,"urban_rate": 0.47},
    "NT": {"name": "Northwest Territories", "weight": 0.001,"urban_rate": 0.46},
    "YT": {"name": "Yukon",                 "weight": 0.001,"urban_rate": 0.74},
    "NU": {"name": "Nunavut",               "weight": 0.001,"urban_rate": 0.32},
}

# ── Dimension: Procedures (real CIHI benchmarks) ──────────────────────────────
PROCEDURES = [
    {"procedure_id": 1, "code": "HIP_REP",  "name": "Hip Replacement",
     "category": "Orthopaedic",   "benchmark_50_days": 91,  "benchmark_90_days": 182,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 2, "code": "KNEE_REP", "name": "Knee Replacement",
     "category": "Orthopaedic",   "benchmark_50_days": 91,  "benchmark_90_days": 182,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 3, "code": "HIP_FRAC", "name": "Hip Fracture Repair",
     "category": "Orthopaedic",   "benchmark_50_days": 1,   "benchmark_90_days": 2,
     "complexity": "urgent",  "requires_specialist": True},
    {"procedure_id": 4, "code": "CATARACT", "name": "Cataract Surgery",
     "category": "Ophthalmology", "benchmark_50_days": 56,  "benchmark_90_days": 112,
     "complexity": "low",    "requires_specialist": True},
    {"procedure_id": 5, "code": "RAD_THER", "name": "Radiation Therapy",
     "category": "Oncology",      "benchmark_50_days": 14,  "benchmark_90_days": 28,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 6, "code": "BYPASS",   "name": "Cardiac Bypass Surgery",
     "category": "Cardiac",       "benchmark_50_days": 7,   "benchmark_90_days": 14,
     "complexity": "urgent",  "requires_specialist": True},
    {"procedure_id": 7, "code": "CANCER_S", "name": "Cancer Surgery",
     "category": "Oncology",      "benchmark_50_days": 14,  "benchmark_90_days": 28,
     "complexity": "high",   "requires_specialist": True},
    {"procedure_id": 8, "code": "MRI_SCAN", "name": "MRI Scan",
     "category": "Diagnostic",    "benchmark_50_days": 15,  "benchmark_90_days": 30,
     "complexity": "low",    "requires_specialist": False},
]

# ── Dimension: Fiscal Periods ─────────────────────────────────────────────────
FISCAL_YEARS = [
    {"period_id": i+1, "fiscal_year": 2014+i,
     "fiscal_year_label": f"{2014+i}-{str(2015+i)[2:]}",
     "is_covid_period": (2014+i) in [2020, 2021],
     "is_post_covid": (2014+i) in [2022, 2023]}
    for i in range(10)
]

# ── Hospital name components ───────────────────────────────────────────────────
HOSPITAL_PREFIXES = [
    "Royal", "St.", "General", "Regional", "Memorial", "University",
    "Community", "Mount", "Civic", "Victoria", "Queen's", "Sunnybrook",
    "North", "South", "East", "West", "Central", "Heritage", "Maple",
]
HOSPITAL_SUFFIXES = [
    "Hospital", "Medical Centre", "Health Centre", "Hospital & Health Sciences Centre",
    "General Hospital", "Regional Hospital", "Memorial Hospital",
]
CITY_NAMES = {
    "ON": ["Toronto","Ottawa","Hamilton","London","Kingston","Sudbury","Thunder Bay",
           "Windsor","Barrie","Brampton","Mississauga","Peterborough","Sault Ste. Marie"],
    "QC": ["Montreal","Quebec City","Laval","Gatineau","Sherbrooke","Saguenay",
           "Trois-Rivieres","Chicoutimi","Rimouski","Rouyn-Noranda"],
    "BC": ["Vancouver","Victoria","Surrey","Kelowna","Kamloops","Prince George",
           "Nanaimo","Abbotsford","Chilliwack","Cranbrook"],
    "AB": ["Calgary","Edmonton","Red Deer","Lethbridge","Medicine Hat","Grande Prairie",
           "Fort McMurray","Lloydminster"],
    "MB": ["Winnipeg","Brandon","Thompson","Portage la Prairie","Steinbach"],
    "SK": ["Saskatoon","Regina","Prince Albert","Moose Jaw","Swift Current"],
    "NS": ["Halifax","Sydney","Truro","New Glasgow","Kentville","Bridgewater"],
    "NB": ["Fredericton","Moncton","Saint John","Bathurst","Edmundston"],
    "NL": ["St. John's","Corner Brook","Gander","Grand Falls-Windsor","Labrador City"],
    "PE": ["Charlottetown","Summerside","Stratford"],
    "NT": ["Yellowknife","Hay River","Fort Smith"],
    "YT": ["Whitehorse","Dawson City"],
    "NU": ["Iqaluit","Rankin Inlet","Arviat"],
}
HEALTH_REGIONS = {
    "ON": ["Toronto Central","Central","East","West","North East","North West","South West"],
    "QC": ["Montreal","Capitale-Nationale","Estrie","Mauricie","Outaouais","Lanaudiere"],
    "BC": ["Fraser","Interior","Northern","Vancouver Coastal","Vancouver Island"],
    "AB": ["Calgary Zone","Edmonton Zone","Central Zone","North Zone","South Zone"],
    "MB": ["Winnipeg","Prairie Mountain","Southern Health","Northern Health","Interlake-Eastern"],
    "SK": ["Regina","Saskatoon","Far North","North","Central","South"],
    "NS": ["Central","Northern","Eastern","Western"],
    "NB": ["Horizon","Vitalite"],
    "NL": ["Eastern","Central","Western","Labrador-Grenfell"],
    "PE": ["Health PEI"],
    "NT": ["NTHSSA"],
    "YT": ["Yukon Health"],
    "NU": ["Nunavut Health"],
}

def generate_hospitals(n=150):
    rows = []
    province_codes = list(PROVINCES.keys())
    weights = [PROVINCES[p]["weight"] for p in province_codes]
    provinces_assigned = RNG.choice(province_codes, size=n, p=weights/np.array(weights).sum())

    for i, prov in enumerate(provinces_assigned):
        pinfo = PROVINCES[prov]
        is_urban = RNG.random() < pinfo["urban_rate"]
        hosp_type = RNG.choice(
            ["Teaching", "Community", "Rural", "Specialty"],
            p=[0.15, 0.55, 0.25, 0.05]
        )
        if not is_urban:
            hosp_type = "Rural"
        city = RNG.choice(CITY_NAMES.get(prov, [prov + " City"]))
        region = RNG.choice(HEALTH_REGIONS.get(prov, ["Regional"]))
        prefix = RNG.choice(HOSPITAL_PREFIXES)
        suffix = RNG.choice(HOSPITAL_SUFFIXES)

        bed_mu = {"Teaching": 450, "Community": 180, "Rural": 60, "Specialty": 120}[hosp_type]
        beds = max(20, int(RNG.normal(bed_mu, bed_mu * 0.3)))

        rows.append({
            "hospital_id":    i + 1,
            "hospital_name":  f"{prefix} {city} {suffix}",
            "province_code":  prov,
            "province_name":  pinfo["name"],
            "health_region":  region,
            "city":           city,
            "hospital_type":  hosp_type,
            "urban_rural":    "Urban" if is_urban else "Rural",
            "bed_count":      beds,
            "established_year": int(RNG.integers(1880, 1990)),
        })
    return pd.DataFrame(rows)

def generate_wait_times(hospitals_df, n_target=180_000):
    records = []
    record_id = 1

    for _, hosp in hospitals_df.iterrows():
        hid     = hosp["hospital_id"]
        prov    = hosp["province_code"]
        htype   = hosp["hospital_type"]
        beds    = hosp["bed_count"]
        is_rural= hosp["urban_rural"] == "Rural"

        # Not every hospital does every procedure
        eligible_procs = []
        for proc in PROCEDURES:
            if proc["complexity"] == "urgent":
                if beds >= 100:
                    eligible_procs.append(proc)
            elif proc["requires_specialist"] and htype == "Rural":
                if RNG.random() < 0.3:
                    eligible_procs.append(proc)
            else:
                eligible_procs.append(proc)

        for proc in eligible_procs:
            for period in FISCAL_YEARS:
                yr   = period["fiscal_year"]
                pid  = period["period_id"]

                # Volume: proportional to beds, with noise
                base_vol = max(5, int(beds * RNG.uniform(0.3, 1.2)))
                if proc["complexity"] == "urgent":
                    base_vol = max(20, int(beds * RNG.uniform(0.8, 1.5)))
                if period["is_covid_period"]:
                    # Elective procedures dropped ~40% during COVID
                    if proc["complexity"] != "urgent":
                        base_vol = int(base_vol * RNG.uniform(0.45, 0.70))
                if period["is_post_covid"]:
                    # Recovery surge
                    base_vol = int(base_vol * RNG.uniform(1.10, 1.35))

                patient_count = max(3, base_vol + int(RNG.normal(0, base_vol * 0.15)))

                # Wait time: based on benchmark, province performance, hospital type
                benchmark_90 = proc["benchmark_90_days"]
                benchmark_50 = proc["benchmark_50_days"]

                # Province performance multiplier (some provinces historically worse)
                prov_mult = {
                    "ON": 1.15, "QC": 1.30, "BC": 1.20, "AB": 1.05,
                    "MB": 1.25, "SK": 1.10, "NS": 1.35, "NB": 1.30,
                    "NL": 1.40, "PE": 1.45, "NT": 1.60, "YT": 1.55, "NU": 1.70,
                }[prov]

                rural_mult = 1.35 if is_rural else 1.0
                covid_mult = 1.45 if period["is_covid_period"] else 1.0
                trend_mult = 1.0 - (yr - 2014) * 0.008  # Slight improvement over time

                p90 = benchmark_90 * prov_mult * rural_mult * covid_mult * trend_mult
                p90 = max(benchmark_90 * 0.6, p90 * RNG.uniform(0.85, 1.20))
                p50 = p90 * RNG.uniform(0.45, 0.60)

                pct_benchmark = max(0, min(100,
                    100 * (benchmark_90 / p90) * RNG.uniform(0.80, 1.05)
                ))

                records.append({
                    "record_id":           record_id,
                    "hospital_id":         hid,
                    "procedure_id":        proc["procedure_id"],
                    "period_id":           pid,
                    "patient_count":       patient_count,
                    "p50_wait_days":       round(p50, 1),
                    "p90_wait_days":       round(p90, 1),
                    "pct_within_benchmark": round(pct_benchmark, 1),
                    "data_completeness":   RNG.choice(["Complete","Partial","Estimated"],
                                             p=[0.85, 0.10, 0.05]),
                })
                record_id += 1

                if len(records) >= n_target:
                    break
            if len(records) >= n_target:
                break
        if len(records) >= n_target:
            break

    return pd.DataFrame(records)

def generate_financials(hospitals_df):
    rows = []
    for _, hosp in hospitals_df.iterrows():
        hid   = hosp["hospital_id"]
        beds  = hosp["bed_count"]
        htype = hosp["hospital_type"]

        base_budget = beds * RNG.uniform(180_000, 280_000)  # ~$200k per bed/year

        for period in FISCAL_YEARS:
            yr  = period["fiscal_year"]
            pid = period["period_id"]

            inflation = 1.0 + (yr - 2014) * 0.028
            covid_surcharge = 1.12 if period["is_covid_period"] else 1.0
            budget = base_budget * inflation * covid_surcharge

            rows.append({
                "hospital_id":    hid,
                "period_id":      pid,
                "fiscal_year":    yr,
                "total_budget_cad":   round(budget, 0),
                "actual_spend_cad":   round(budget * RNG.uniform(0.93, 1.08), 0),
                "nursing_fte":    max(10, int(beds * RNG.uniform(1.2, 1.8))),
                "physician_fte":  max(3,  int(beds * RNG.uniform(0.15, 0.30))),
                "admin_fte":      max(5,  int(beds * RNG.uniform(0.20, 0.40))),
                "or_rooms":       max(1,  int(beds / RNG.uniform(25, 40))),
            })
    return pd.DataFrame(rows)

def main():
    os.makedirs("data", exist_ok=True)

    print("Generating hospitals …")
    hospitals = generate_hospitals(150)
    hospitals.to_csv("data/dim_hospitals.csv", index=False)
    print(f"  ✔  dim_hospitals.csv — {len(hospitals):,} rows")

    print("Generating procedures dimension …")
    procs_df = pd.DataFrame(PROCEDURES)
    procs_df.to_csv("data/dim_procedures.csv", index=False)
    print(f"  ✔  dim_procedures.csv — {len(procs_df):,} rows")

    print("Generating fiscal periods …")
    periods_df = pd.DataFrame(FISCAL_YEARS)
    periods_df.to_csv("data/dim_periods.csv", index=False)
    print(f"  ✔  dim_periods.csv — {len(periods_df):,} rows")

    print("Generating wait time records (~180k rows) …")
    wt = generate_wait_times(hospitals)
    wt.to_csv("data/fact_wait_times.csv", index=False)
    print(f"  ✔  fact_wait_times.csv — {len(wt):,} rows")

    print("Generating hospital financials …")
    fin = generate_financials(hospitals)
    fin.to_csv("data/fact_financials.csv", index=False)
    print(f"  ✔  fact_financials.csv — {len(fin):,} rows")

    print("\nDataset summary:")
    print(f"  Hospitals:       {len(hospitals):,}")
    print(f"  Procedures:      {len(procs_df):,}")
    print(f"  Fiscal periods:  {len(periods_df):,}")
    print(f"  Wait records:    {len(wt):,}")
    print(f"  Financial rows:  {len(fin):,}")

if __name__ == "__main__":
    main()
