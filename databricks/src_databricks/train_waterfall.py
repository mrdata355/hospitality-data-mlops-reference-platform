from __future__ import annotations

from datetime import datetime, timezone

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from pyspark.sql import Row
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from common import parse_runtime_args, table

cfg = parse_runtime_args(include_acceptance=True)

FEATURES = [
    "lag_1w",
    "lag_4w",
    "lag_13w",
    "lag_52w",
    "rolling_mean_4w",
    "rolling_mean_13w",
    "campaign_intensity",
    "week_of_year",
    "season_sin",
    "season_cos",
    "month",
    "quarter",
    "capacity_units",
    "resort_code",
]
TARGET = "arrivals"
MODEL_NAME = table(cfg.catalog, "models", "waterfall_forecast_model")

pdf = (
    spark.table(table(cfg.catalog, "features", "waterfall_resort_week_features"))
    .orderBy("week_start")
    .toPandas()
)
pdf["week_start"] = pd.to_datetime(pdf["week_start"])
if pdf.empty:
    raise RuntimeError("No waterfall feature rows are available for training.")

cutoff = pdf.week_start.quantile(0.80)
train = pdf[pdf.week_start < cutoff]
valid = pdf[pdf.week_start >= cutoff]
if train.empty or valid.empty:
    raise RuntimeError("Chronological split produced an empty training or validation set.")

with mlflow.start_run(run_name="waterfall_forecast_training") as run:
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(train[FEATURES], train[TARGET])
    predictions = model.predict(valid[FEATURES])
    baseline = valid["lag_52w"].to_numpy()
    actual = valid[TARGET].to_numpy()

    mae = mean_absolute_error(actual, predictions)
    wape = abs(actual - predictions).sum() / max(abs(actual).sum(), 1)
    baseline_wape = abs(actual - baseline).sum() / max(abs(actual).sum(), 1)
    improves_baseline = wape <= baseline_wape
    passes_absolute_gate = wape <= cfg.max_wape
    accepted = passes_absolute_gate and (
        improves_baseline or not cfg.require_baseline_improvement
    )

    mlflow.log_params(
        {
            "n_estimators": 300,
            "max_depth": 10,
            "min_samples_leaf": 2,
            "validation_cutoff": str(cutoff),
            "catalog": cfg.catalog,
        }
    )
    mlflow.log_metrics(
        {
            "valid_mae": float(mae),
            "valid_wape": float(wape),
            "seasonal_baseline_wape": float(baseline_wape),
            "accepted": int(accepted),
        }
    )
    mlflow.set_tags(
        {
            "business_use_case": "waterfall_forecast",
            "prediction_grain": "resort_id + week_start",
            "designed_by": "Kellon Lewis",
            "release_status": "candidate",
            "acceptance_gate": "passed" if accepted else "failed",
        }
    )
    signature = mlflow.models.infer_signature(
        train[FEATURES].head(100), model.predict(train[FEATURES].head(100))
    )
    model_info = mlflow.sklearn.log_model(
        model,
        "model",
        signature=signature,
        registered_model_name=MODEL_NAME,
    )

client = MlflowClient()
versions = [
    mv
    for mv in client.search_model_versions(f"name='{MODEL_NAME}'")
    if mv.run_id == run.info.run_id
]
if not versions:
    raise RuntimeError("The registered model version could not be resolved for this run.")
model_version = max(versions, key=lambda mv: int(mv.version)).version

candidate = Row(
    model_name=MODEL_NAME,
    model_version=str(model_version),
    run_id=run.info.run_id,
    validation_cutoff=str(cutoff),
    valid_mae=float(mae),
    valid_wape=float(wape),
    baseline_wape=float(baseline_wape),
    accepted=bool(accepted),
    created_at=datetime.now(timezone.utc),
)
(
    spark.createDataFrame([candidate])
    .write.mode("append")
    .saveAsTable(table(cfg.catalog, "ops", "model_candidate_evidence"))
)

if not accepted:
    raise RuntimeError(
        f"Candidate rejected: wape={wape:.4f}, baseline={baseline_wape:.4f}, "
        f"max_wape={cfg.max_wape:.4f}. The active alias was not changed."
    )
