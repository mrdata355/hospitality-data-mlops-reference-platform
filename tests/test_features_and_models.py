import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_member_features_are_one_row_per_grain():
    frame = pd.read_csv(ROOT / "data/gold/member_month_features.csv")
    assert not frame.duplicated(["member_id", "as_of_month"]).any()
    assert "churn_label" not in [
        "tenure_months", "points_earned_12m", "points_redeemed_12m", "points_expired_12m",
        "points_utilization_rate", "expired_share", "stays_12m", "room_nights_12m",
        "net_room_revenue_12m", "service_cases_90d", "escalated_cases_90d",
        "avg_resolution_hours_90d", "days_since_last_booking", "member_tier", "home_market",
    ]


def test_waterfall_lags_have_no_nulls():
    frame = pd.read_csv(ROOT / "data/gold/waterfall_resort_week_features.csv")
    columns = ["lag_1w", "lag_4w", "lag_13w", "lag_52w", "rolling_mean_4w", "rolling_mean_13w"]
    assert frame[columns].isna().sum().sum() == 0


def test_model_acceptance_gates():
    churn = json.load(open(ROOT / "artifacts/metrics/member_churn_metrics.json"))
    forecast = json.load(open(ROOT / "artifacts/metrics/waterfall_forecast_metrics.json"))
    assert churn["roc_auc"] >= 0.75
    assert forecast["wape"] <= 0.30
    assert forecast["wape"] <= forecast["baseline_wape"]
