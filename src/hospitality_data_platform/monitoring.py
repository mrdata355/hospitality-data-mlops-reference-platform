from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import GOLD, MONITORING, PREDICTIONS


def population_stability_index(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    boundaries = np.quantile(expected, np.linspace(0, 1, bins + 1))
    boundaries[0], boundaries[-1] = -np.inf, np.inf
    expected_bins = pd.cut(expected, boundaries, duplicates="drop").value_counts(normalize=True, sort=False)
    actual_bins = pd.cut(actual, boundaries, duplicates="drop").value_counts(normalize=True, sort=False)
    expected_bins, actual_bins = expected_bins.align(actual_bins, fill_value=0.0001)
    e = expected_bins.clip(lower=0.0001)
    a = actual_bins.clip(lower=0.0001)
    return float(((a - e) * np.log(a / e)).sum())


def run_monitoring() -> dict[str, float]:
    features = pd.read_csv(GOLD / "member_month_features.csv")
    scores = pd.read_csv(PREDICTIONS / "member_churn_scores.csv")
    forecast = pd.read_csv(PREDICTIONS / "waterfall_forecast_resort_week.csv")

    split = int(len(features) * 0.75)
    expected = features.iloc[:split].days_since_last_booking
    actual = features.iloc[split:].days_since_last_booking
    psi = population_stability_index(expected, actual)

    wape = float(forecast.absolute_error.sum() / max(forecast.actual.abs().sum(), 1.0))
    bias = float((forecast.prediction - forecast.actual).mean())
    high_risk_share = float((scores.risk_band == "HIGH").mean())

    result = {
        "days_since_last_booking_psi": psi,
        "forecast_wape": wape,
        "forecast_bias": bias,
        "high_risk_share": high_risk_share,
        "feature_drift_status": "PASS" if psi < 0.25 else "WARN",
        "forecast_accuracy_status": "PASS" if wape < 0.35 else "WARN",
    }
    pd.DataFrame([result]).to_csv(MONITORING / "model_health.csv", index=False)
    (MONITORING / "model_health.json").write_text(json.dumps(result, indent=2))
    return result
