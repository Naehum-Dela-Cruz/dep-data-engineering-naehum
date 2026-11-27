"""Path B Analytics & KPI Export Pipeline.

Reads the analytical master dataset produced by scripts/transform.py,
computes the Week 17 lead-time & search-buzz segmentation and Week 18 KPIs,
and saves reusable CSV outputs under output/.
"""

from pathlib import Path
import pandas as pd
from scipy.stats import spearmanr


MASTER_PATH = Path("data/processed/masskara/analysis/master.csv")
OUTPUT_DIR = Path("output")


def compute_path_b_outputs(master_path: Path = MASTER_PATH, output_dir: Path = OUTPUT_DIR) -> None:
    """Compute segmentation and KPI tables and write them to output_dir."""
    df = pd.read_csv(master_path, parse_dates=["date_collected"])
    df = df.sort_values("date_collected").reset_index(drop=True)

    # Pre-festival window (days_to_festival > 0) excludes post-festival rolling-only rows
    pre_fest = df[df["days_to_festival"] > 0].copy().reset_index(drop=True)
    if pre_fest.empty:
        raise ValueError("No pre-festival rows (days_to_festival > 0) found in master.csv.")

    # Lead-time cohorts (Week 17)
    cohort_bins = [-1, 7, 20, 1000]
    cohort_labels = ["Surge Window (<=7d)", "Mid Window (8-20d)", "Advance Window (>20d)"]
    pre_fest["lead_cohort"] = pd.cut(
        pre_fest["days_to_festival"], bins=cohort_bins, labels=cohort_labels
    )

    # Search buzz tier (Week 17)
    pre_fest["search_buzz_tier"] = pre_fest["trend_search_score"].apply(
        lambda s: "High Buzz (>=67)" if pd.notna(s) and s >= 67 else "Low Buzz (<67)"
    )

    # KPI 1: Festival Price Premium Ratio (FPPR %)
    pre_fest["flight_fppr_pct"] = (
        (pre_fest["flight_fest_median_price"] - pre_fest["flight_rolling_median_price"])
        / pre_fest["flight_rolling_median_price"]
        * 100
    )
    pre_fest["hotel_fppr_pct"] = (
        (pre_fest["hotel_fest_median_price"] - pre_fest["hotel_rolling_median_price"])
        / pre_fest["hotel_rolling_median_price"]
        * 100
    )

    # KPI 2: Lead-Time Booking Penalty Index (LBPI)
    advance_mask = pre_fest["days_to_festival"] > 20
    advance_min_baseline = pre_fest.loc[advance_mask, "flight_fest_min_price"].median()
    pre_fest["flight_lbpi"] = pre_fest["flight_fest_min_price"] / advance_min_baseline

    # KPI 3: Lagged Spearman correlation (0d..3d)
    lag_rows = []
    for lag in [0, 1, 2, 3]:
        trend_col = "trend_search_score" if lag == 0 else f"trend_score_lag_{lag}d"
        sub_f = pre_fest.dropna(subset=["flight_fest_median_price", trend_col])
        rho_f, pval_f = spearmanr(sub_f[trend_col], sub_f["flight_fest_median_price"])

        sub_h = pre_fest.dropna(subset=["hotel_fest_median_price", trend_col])
        rho_h, pval_h = spearmanr(sub_h[trend_col], sub_h["hotel_fest_median_price"])

        lag_rows.append(
            {
                "lag_days": lag,
                "flight_spearman_rho": round(float(rho_f), 4),
                "flight_p_value": round(float(pval_f), 6),
                "hotel_spearman_rho": round(float(rho_h), 4),
                "hotel_p_value": round(float(pval_h), 6),
            }
        )
    lag_df = pd.DataFrame(lag_rows)

    # Executive KPI Cohort Scorecard (Week 18)
    scorecard_df = (
        pre_fest.groupby("lead_cohort", observed=False)
        .agg(
            observations=("date_collected", "count"),
            avg_days_out=("days_to_festival", "mean"),
            flight_fest_median_php=("flight_fest_median_price", "median"),
            hotel_fest_median_php=("hotel_fest_median_price", "median"),
            flight_fppr_median_pct=("flight_fppr_pct", "median"),
            hotel_fppr_median_pct=("hotel_fppr_pct", "median"),
            flight_lbpi_median=("flight_lbpi", "median"),
            flight_lbpi_max=("flight_lbpi", "max"),
            flight_daily_velocity_avg_php=("flight_median_change_1d", "mean"),
            hotel_daily_velocity_avg_php=("hotel_median_change_1d", "mean"),
            avg_search_score=("trend_search_score", "mean"),
        )
        .reset_index()
        .round(2)
    )

    # 2D Segmentation: Lead Cohort x Search Buzz Tier (Week 17)
    seg_df = (
        pre_fest.groupby(["lead_cohort", "search_buzz_tier"], observed=False)
        .agg(
            observations=("date_collected", "count"),
            flight_median_php=("flight_fest_median_price", "median"),
            flight_mean_php=("flight_fest_median_price", "mean"),
            hotel_median_php=("hotel_fest_median_price", "median"),
            avg_search_score=("trend_search_score", "mean"),
        )
        .reset_index()
        .round(2)
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    daily_cols = [
        "date_collected",
        "days_to_festival",
        "lead_cohort",
        "search_buzz_tier",
        "trend_search_score",
        "flight_fest_min_price",
        "flight_fest_median_price",
        "hotel_fest_median_price",
        "flight_fppr_pct",
        "hotel_fppr_pct",
        "flight_lbpi",
        "flight_median_change_1d",
        "hotel_median_change_1d",
    ]
    pre_fest[daily_cols].round(4).to_csv(output_dir / "kpi_daily_metrics.csv", index=False)
    scorecard_df.to_csv(output_dir / "kpi_cohort_scorecard.csv", index=False)
    lag_df.to_csv(output_dir / "kpi_lag_correlation.csv", index=False)
    seg_df.to_csv(output_dir / "segmentation_cohort_buzz_summary.csv", index=False)

    print(f"Saved Path B outputs to {output_dir}/ ({len(pre_fest)} pre-festival days).")


if __name__ == "__main__":
    compute_path_b_outputs()
