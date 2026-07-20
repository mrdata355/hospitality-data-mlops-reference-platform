from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SAMPLE_DATA = EXAMPLES / "sample_data"
SAMPLE_OUTPUTS = EXAMPLES / "sample_outputs"
SAMPLE_ROWS = 25


def _export_csv(
    source: Path,
    destination: Path,
    columns: list[str],
    sort_by: list[str],
    row_limit: int = SAMPLE_ROWS,
) -> None:
    frame = pd.read_csv(source)
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing expected columns: {missing}")
    sample = frame.loc[:, columns].sort_values(sort_by).head(row_limit).reset_index(drop=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(destination, index=False, lineterminator="\n", float_format="%.6f")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def export_examples() -> None:
    SAMPLE_DATA.mkdir(parents=True, exist_ok=True)
    SAMPLE_OUTPUTS.mkdir(parents=True, exist_ok=True)

    _export_csv(
        ROOT / "data/raw/members.csv",
        SAMPLE_DATA / "members_sample.csv",
        ["member_id", "member_tier", "home_market", "member_since_date", "active_flag"],
        ["member_id"],
    )
    _export_csv(
        ROOT / "data/raw/reservations.csv",
        SAMPLE_DATA / "reservations_sample.csv",
        [
            "reservation_id",
            "member_id",
            "resort_id",
            "booking_date",
            "check_in_date",
            "check_out_date",
            "reservation_status",
            "room_nights",
            "points_redeemed",
            "net_room_revenue",
        ],
        ["reservation_id"],
    )
    _export_csv(
        ROOT / "data/raw/points_transactions.csv",
        SAMPLE_DATA / "points_transactions_sample.csv",
        ["transaction_id", "member_id", "transaction_date", "transaction_type", "points_amount"],
        ["transaction_id"],
    )
    _export_csv(
        ROOT / "data/raw/tour_events.csv",
        SAMPLE_DATA / "tour_events_sample.csv",
        ["tour_id", "package_id", "prospect_id", "tour_date", "tour_status", "market"],
        ["tour_id"],
    )
    _export_csv(
        ROOT / "data/raw/labor_shifts.csv",
        SAMPLE_DATA / "labor_shifts_sample.csv",
        ["shift_id", "resort_id", "employee_id", "work_date", "labor_hours", "payroll_cost"],
        ["shift_id"],
    )

    _export_csv(
        ROOT / "data/gold/member_month_features.csv",
        SAMPLE_OUTPUTS / "member_month_features_sample.csv",
        [
            "member_id",
            "member_tier",
            "home_market",
            "as_of_month",
            "tenure_months",
            "points_earned_12m",
            "points_redeemed_12m",
            "points_expired_12m",
            "points_utilization_rate",
            "expired_share",
            "stays_12m",
            "room_nights_12m",
            "net_room_revenue_12m",
            "avg_booking_lead_days_12m",
            "service_cases_90d",
            "escalated_cases_90d",
            "avg_resolution_hours_90d",
            "days_since_last_booking",
            "churn_label",
        ],
        ["member_id", "as_of_month"],
    )
    _export_csv(
        ROOT / "artifacts/predictions/waterfall_forecast_resort_week.csv",
        SAMPLE_OUTPUTS / "waterfall_forecast_sample.csv",
        [
            "resort_id",
            "forecast_week_start",
            "market",
            "actual",
            "prediction",
            "absolute_error",
            "forecast_run_id",
            "model_name",
            "model_version_or_alias",
            "horizon_weeks",
        ],
        ["forecast_week_start", "resort_id"],
    )
    _export_csv(
        ROOT / "data/gold/data_quality_results.csv",
        SAMPLE_OUTPUTS / "data_quality_results.csv",
        ["table_name", "check_name", "status", "observed_value", "threshold_value", "details"],
        ["table_name", "check_name"],
        row_limit=10_000,
    )

    churn = _load_json(ROOT / "artifacts/metrics/member_churn_metrics.json")
    forecast = _load_json(ROOT / "artifacts/metrics/waterfall_forecast_metrics.json")
    monitoring = _load_json(ROOT / "artifacts/monitoring/model_health.json")
    source_counts = {
        name: int(len(pd.read_csv(ROOT / f"data/raw/{name}.csv")))
        for name in [
            "members",
            "resorts",
            "campaigns",
            "reservations",
            "resort_stays",
            "points_transactions",
            "vacation_packages",
            "tour_events",
            "sales_contracts",
            "marketing_events",
            "service_cases",
            "labor_shifts",
        ]
    }
    summary = {
        "data_profile": {
            "source_domains": len(source_counts),
            "source_row_counts": source_counts,
            "synthetic_data_only": True,
        },
        "member_risk": {
            "roc_auc": churn["roc_auc"],
            "accuracy": churn["accuracy"],
            "precision": churn["precision"],
            "recall": churn["recall"],
            "f1": churn["f1"],
            "test_rows": churn["test_rows"],
        },
        "waterfall_forecast": {
            "mae": forecast["mae"],
            "wape": forecast["wape"],
            "baseline_wape": forecast["baseline_wape"],
            "forecast_bias": forecast["forecast_bias"],
            "test_rows": forecast["test_rows"],
            "cutoff_week": forecast["cutoff_week"],
        },
        "monitoring": monitoring,
        "acceptance": {
            "member_risk_roc_auc_at_least_0_75": churn["roc_auc"] >= 0.75,
            "forecast_wape_at_most_0_30": forecast["wape"] <= 0.30,
            "forecast_beats_seasonal_baseline": forecast["wape"] <= forecast["baseline_wape"],
        },
    }
    (SAMPLE_OUTPUTS / "validation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    export_examples()
