"""
src/eda.py
==========
Exploratory Data Analysis — generates all charts for the portfolio.
Saves publication-quality figures to figures/ directory.

Run: python src/eda.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

os.makedirs("figures", exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#fafafa",
    "axes.facecolor":   "#fafafa",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.color":       "#cccccc",
    "font.family":      "DejaVu Sans",
    "font.size":        10,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.labelsize":   10,
})

NAVY  = "#0d1b2a"
GOLD  = "#e8b86d"
TEAL  = "#2196a6"
RED   = "#e06c75"
GREEN = "#52c987"
GRAY  = "#8a99a8"

PROVINCE_COLORS = {
    "ON": "#e8b86d", "QC": "#e06c75", "BC": "#52c987", "AB": "#2196a6",
    "MB": "#9c59d1", "SK": "#ff7043", "NS": "#26a69a", "NB": "#ec407a",
    "NL": "#7e57c2", "PE": "#29b6f6",
}

def load_data():
    hospitals  = pd.read_csv("data/dim_hospitals.csv")
    procedures = pd.read_csv("data/dim_procedures.csv")
    periods    = pd.read_csv("data/dim_periods.csv")
    wt         = pd.read_csv("data/fact_wait_times.csv")
    fin        = pd.read_csv("data/fact_financials.csv")
    return hospitals, procedures, periods, wt, fin

def fig1_national_trend(wt, periods):
    """National wait time trend 2014-2023 with COVID annotation."""
    df = (wt.merge(periods, on="period_id")
            .groupby(["fiscal_year", "fiscal_year_label", "is_covid_period"])
            .agg(avg_p90=("p90_wait_days","mean"),
                 avg_bench=("pct_within_benchmark","mean"),
                 total_patients=("patient_count","sum"))
            .reset_index())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Canadian Hospital Wait Times — National Trend (2014–2023)",
                 fontsize=15, fontweight="bold", color=NAVY, y=1.02)

    # Left: P90 wait time
    ax = axes[0]
    colors = [RED if c else TEAL for c in df["is_covid_period"]]
    ax.bar(df["fiscal_year_label"], df["avg_p90"], color=colors, alpha=0.85, width=0.7)
    ax.axhspan(df["avg_p90"].min() - 5, df["avg_p90"].max() + 5,
               where=[c for c in df["is_covid_period"]], alpha=0, color="none")
    # COVID annotation
    covid_years = df[df["is_covid_period"]]
    if len(covid_years):
        ax.axvspan(
            covid_years["fiscal_year_label"].iloc[0],
            covid_years["fiscal_year_label"].iloc[-1],
            alpha=0.12, color=RED, label="COVID Period"
        )
    ax.set_title("Avg 90th Percentile Wait Time (Days)")
    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Days")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    # Right: Benchmark compliance
    ax2 = axes[1]
    ax2.plot(df["fiscal_year_label"], df["avg_bench"],
             color=TEAL, linewidth=2.5, marker="o", markersize=6, label="Benchmark %")
    ax2.fill_between(df["fiscal_year_label"], df["avg_bench"],
                     alpha=0.15, color=TEAL)
    ax2.axhline(90, color=GREEN, linestyle="--", linewidth=1.5, label="90% target")
    covid_idx = df[df["is_covid_period"]].index.tolist()
    for idx in covid_idx:
        ax2.axvline(df.loc[idx, "fiscal_year_label"],
                    color=RED, alpha=0.3, linewidth=8)
    ax2.set_title("Avg % Patients Within Benchmark")
    ax2.set_xlabel("Fiscal Year")
    ax2.set_ylabel("% Within Benchmark")
    ax2.tick_params(axis="x", rotation=45)
    ax2.set_ylim(50, 105)
    ax2.legend()

    plt.tight_layout()
    plt.savefig("figures/01_national_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/01_national_trend.png")

def fig2_province_heatmap(wt, hospitals, periods):
    """Province × Fiscal Year heatmap of benchmark compliance."""
    df = (wt.merge(hospitals[["hospital_id","province_code"]], on="hospital_id")
            .merge(periods[["period_id","fiscal_year_label"]], on="period_id")
            .groupby(["province_code","fiscal_year_label"])
            ["pct_within_benchmark"].mean()
            .reset_index())

    pivot = df.pivot(index="province_code", columns="fiscal_year_label",
                     values="pct_within_benchmark")

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=55, vmax=100)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Province × Year Benchmark Compliance Heatmap (%)",
                 fontsize=14, fontweight="bold", pad=15)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}",
                        ha="center", va="center",
                        fontsize=8,
                        color="white" if val < 72 else "black")

    plt.colorbar(im, ax=ax, label="% Within Benchmark", fraction=0.03)
    plt.tight_layout()
    plt.savefig("figures/02_province_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/02_province_heatmap.png")

def fig3_procedure_boxplot(wt, procedures):
    """Box plot of P90 wait time distribution per procedure."""
    df = wt.merge(procedures[["procedure_id","name","benchmark_90_days"]],
                  on="procedure_id")

    order = (df.groupby("name")["p90_wait_days"].median()
               .sort_values(ascending=False).index)

    fig, ax = plt.subplots(figsize=(14, 6))
    bp_data = [df[df["name"] == proc]["p90_wait_days"].dropna().values
               for proc in order]
    bp = ax.boxplot(bp_data, vert=True, patch_artist=True,
                    medianprops=dict(color=NAVY, linewidth=2),
                    flierprops=dict(marker=".", markersize=2, alpha=0.3))

    palette = [TEAL, GOLD, GREEN, RED, "#9c59d1", "#ff7043", "#26a69a", "#ec407a"]
    for patch, color in zip(bp["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    # Benchmark line per procedure
    benchmarks = {row["name"]: row["benchmark_90_days"]
                  for _, row in procedures.iterrows()}
    for i, proc in enumerate(order):
        bench = benchmarks.get(proc, None)
        if bench:
            ax.plot([i + 0.6, i + 1.4], [bench, bench],
                    color=RED, linewidth=1.5, linestyle="--", alpha=0.8)

    ax.set_xticklabels(order, rotation=30, ha="right")
    ax.set_ylabel("90th Percentile Wait (Days)")
    ax.set_title("P90 Wait Time Distribution by Procedure
(dashed red = CIHI benchmark)",
                 fontsize=13, fontweight="bold")

    bench_line = mpatches.Patch(color=RED, label="CIHI Benchmark Target", linestyle="--")
    ax.legend(handles=[bench_line], loc="upper right")
    plt.tight_layout()
    plt.savefig("figures/03_procedure_boxplot.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/03_procedure_boxplot.png")

def fig4_urban_rural_equity(wt, hospitals, procedures):
    """Urban vs Rural wait time gap by procedure."""
    df = (wt.merge(hospitals[["hospital_id","urban_rural"]], on="hospital_id")
            .merge(procedures[["procedure_id","name"]], on="procedure_id")
            .groupby(["urban_rural","name"])["p90_wait_days"]
            .mean().reset_index())

    urban  = df[df["urban_rural"] == "Urban"].set_index("name")["p90_wait_days"]
    rural  = df[df["urban_rural"] == "Rural"].set_index("name")["p90_wait_days"]
    procs  = urban.index.intersection(rural.index)
    gap    = (rural[procs] - urban[procs]).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [GREEN if g < 0 else RED for g in gap.values]
    ax.barh(gap.index, gap.values, color=colors, alpha=0.8)
    ax.axvline(0, color=NAVY, linewidth=1.2)
    ax.set_xlabel("Rural − Urban Wait Days (Equity Gap)")
    ax.set_title("Urban–Rural Wait Time Equity Gap by Procedure
(positive = Rural waits longer)",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(gap.min() - 10, gap.max() + 20)

    for i, (val, idx) in enumerate(zip(gap.values, gap.index)):
        ax.text(val + 1.5, i, f"+{val:.0f}d" if val >= 0 else f"{val:.0f}d",
                va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig("figures/04_urban_rural_equity.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/04_urban_rural_equity.png")

def fig5_volume_vs_performance(wt, hospitals):
    """Scatter: hospital volume vs benchmark performance (coloured by type)."""
    df = (wt.merge(hospitals[["hospital_id","hospital_type","province_code",
                               "urban_rural","bed_count"]], on="hospital_id")
            .groupby(["hospital_id","hospital_type","province_code",
                      "urban_rural","bed_count"])
            .agg(total_patients=("patient_count","sum"),
                 avg_benchmark=("pct_within_benchmark","mean"))
            .reset_index())

    type_colors = {"Teaching": TEAL, "Community": GOLD,
                   "Rural": RED, "Specialty": GREEN}
    fig, ax = plt.subplots(figsize=(11, 7))

    for htype, group in df.groupby("hospital_type"):
        ax.scatter(group["total_patients"], group["avg_benchmark"],
                   color=type_colors.get(htype, GRAY),
                   alpha=0.6, s=group["bed_count"] / 5,
                   label=htype, edgecolors="white", linewidths=0.4)

    ax.axhline(90, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7,
               label="90% benchmark target")
    ax.set_xlabel("Total Patients Treated (10-year sum)")
    ax.set_ylabel("Avg % Patients Within Benchmark")
    ax.set_title("Hospital Volume vs Performance
(bubble size = bed count)",
                 fontsize=13, fontweight="bold")
    ax.legend(title="Hospital Type", loc="lower right")
    plt.tight_layout()
    plt.savefig("figures/05_volume_vs_performance.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✔  figures/05_volume_vs_performance.png")

def main():
    print("Loading data …")
    hospitals, procedures, periods, wt, fin = load_data()
    print(f"  {len(wt):,} wait time records loaded")

    print("\nGenerating figures …")
    fig1_national_trend(wt, periods)
    fig2_province_heatmap(wt, hospitals, periods)
    fig3_procedure_boxplot(wt, procedures)
    fig4_urban_rural_equity(wt, hospitals, procedures)
    fig5_volume_vs_performance(wt, hospitals)

    print(f"\n✔  All figures saved to figures/")

if __name__ == "__main__":
    main()
