from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_reviewer_sample_pack_exists() -> None:
    required = [
        "sample_data/members_sample.csv",
        "sample_data/reservations_sample.csv",
        "sample_data/points_transactions_sample.csv",
        "sample_data/tour_events_sample.csv",
        "sample_data/labor_shifts_sample.csv",
        "sample_outputs/member_month_features_sample.csv",
        "sample_outputs/waterfall_forecast_sample.csv",
        "sample_outputs/data_quality_results.csv",
        "sample_outputs/validation_summary.json",
    ]
    for relative_path in required:
        assert (EXAMPLES / relative_path).is_file(), relative_path


def test_samples_are_compact_and_public_safe() -> None:
    forbidden_columns = {"first_name", "last_name", "email", "phone", "ssn", "token", "password"}
    for path in (EXAMPLES / "sample_data").glob("*.csv"):
        frame = pd.read_csv(path)
        assert 1 <= len(frame) <= 25, path.name
        assert not forbidden_columns.intersection({column.lower() for column in frame.columns})


def test_feature_and_forecast_grains_are_unique() -> None:
    features = pd.read_csv(EXAMPLES / "sample_outputs/member_month_features_sample.csv")
    forecasts = pd.read_csv(EXAMPLES / "sample_outputs/waterfall_forecast_sample.csv")
    assert not features.duplicated(["member_id", "as_of_month"]).any()
    assert not forecasts.duplicated(["resort_id", "forecast_week_start", "forecast_run_id"]).any()


def test_sample_quality_results_pass() -> None:
    quality = pd.read_csv(EXAMPLES / "sample_outputs/data_quality_results.csv")
    assert set(quality["status"]) == {"PASS"}


def test_sample_validation_summary_meets_acceptance_gates() -> None:
    summary = json.loads((EXAMPLES / "sample_outputs/validation_summary.json").read_text())
    assert summary["data_profile"]["source_domains"] == 12
    assert summary["data_profile"]["synthetic_data_only"] is True
    assert all(summary["acceptance"].values())
