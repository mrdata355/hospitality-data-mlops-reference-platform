from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, mean_absolute_error, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import METRICS, MODELS, PREDICTIONS, SEED

CHURN_NUMERIC = ["tenure_months", "points_earned_12m", "points_redeemed_12m", "points_expired_12m", "points_utilization_rate", "expired_share", "stays_12m", "room_nights_12m", "net_room_revenue_12m", "service_cases_90d", "escalated_cases_90d", "avg_resolution_hours_90d", "days_since_last_booking"]
CHURN_CATEGORICAL = ["member_tier", "home_market"]


def train_churn_model(features: pd.DataFrame) -> dict[str, float]:
    train, test = train_test_split(features, test_size=0.25, random_state=SEED, stratify=features["churn_label"])
    preprocessing = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), CHURN_NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CHURN_CATEGORICAL),
    ])
    model = Pipeline([("preprocess", preprocessing), ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED))])
    model.fit(train[CHURN_NUMERIC + CHURN_CATEGORICAL], train.churn_label)
    probability = model.predict_proba(test[CHURN_NUMERIC + CHURN_CATEGORICAL])[:, 1]
    prediction = (probability >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(test.churn_label, probability)),
        "accuracy": float(accuracy_score(test.churn_label, prediction)),
        "precision": float(precision_score(test.churn_label, prediction, zero_division=0)),
        "recall": float(recall_score(test.churn_label, prediction, zero_division=0)),
        "f1": float(f1_score(test.churn_label, prediction, zero_division=0)),
        "test_rows": int(len(test)),
        "positive_rate": float(test.churn_label.mean()),
        "confusion_matrix": confusion_matrix(test.churn_label, prediction).tolist(),
    }
    joblib.dump(model, MODELS / "member_churn_model.joblib")
    scored = test[["member_id", "member_tier", "home_market", "churn_label"]].copy()
    scored["churn_probability"] = probability
    scored["risk_band"] = pd.cut(scored.churn_probability, bins=[-0.01, 0.35, 0.65, 1.0], labels=["LOW", "MEDIUM", "HIGH"])
    scored.to_csv(PREDICTIONS / "member_churn_scores.csv", index=False)
    (METRICS / "member_churn_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


FORECAST_FEATURES = ["lag_1w", "lag_4w", "lag_13w", "lag_52w", "rolling_mean_4w", "rolling_mean_13w", "campaign_intensity", "week_of_year", "season_sin", "season_cos", "month", "quarter", "capacity_units", "resort_code"]


def train_waterfall_model(features: pd.DataFrame) -> dict[str, float]:
    features = features.sort_values("week_start").copy()
    dates = pd.to_datetime(features.week_start)
    cutoff = dates.quantile(0.80)
    train = features[dates < cutoff]
    test = features[dates >= cutoff]

    model = RandomForestRegressor(n_estimators=180, max_depth=10, min_samples_leaf=2, random_state=SEED, n_jobs=1)
    model.fit(train[FORECAST_FEATURES], train.arrivals)
    prediction = np.clip(model.predict(test[FORECAST_FEATURES]), 0, None)
    baseline = test.lag_52w.to_numpy()
    actual = test.arrivals.to_numpy()

    def wape(y: np.ndarray, p: np.ndarray) -> float:
        return float(np.abs(y - p).sum() / max(np.abs(y).sum(), 1.0))

    metrics = {
        "mae": float(mean_absolute_error(actual, prediction)),
        "wape": wape(actual, prediction),
        "forecast_bias": float(np.mean(prediction - actual)),
        "baseline_wape": wape(actual, baseline),
        "test_rows": int(len(test)),
        "cutoff_week": str(pd.Timestamp(cutoff).date()),
    }
    joblib.dump(model, MODELS / "waterfall_forecast_model.joblib")
    forecast = test[["resort_id", "week_start", "market", "arrivals"]].copy().rename(columns={"arrivals": "actual", "week_start": "forecast_week_start"})
    forecast["prediction"] = prediction
    forecast["absolute_error"] = np.abs(forecast.actual - forecast.prediction)
    forecast["forecast_run_id"] = "local_release_2026_07_10_001"
    forecast["model_name"] = "waterfall_forecast_model"
    forecast["model_version_or_alias"] = "Champion"
    forecast["horizon_weeks"] = 1
    forecast["scored_at"] = pd.Timestamp.utcnow().isoformat()
    forecast.to_csv(PREDICTIONS / "waterfall_forecast_resort_week.csv", index=False)
    (METRICS / "waterfall_forecast_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics
