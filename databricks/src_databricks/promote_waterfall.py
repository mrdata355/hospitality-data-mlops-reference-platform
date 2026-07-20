from __future__ import annotations

from datetime import datetime, timezone

from mlflow import MlflowClient
from pyspark.sql import Row, functions as F

from common import parse_runtime_args, table

cfg = parse_runtime_args(include_model_alias=True)
MODEL_NAME = table(cfg.catalog, "models", "waterfall_forecast_model")
EVIDENCE_TABLE = table(cfg.catalog, "ops", "model_candidate_evidence")
PROMOTION_TABLE = table(cfg.catalog, "ops", "model_promotion_history")

candidate_rows = (
    spark.table(EVIDENCE_TABLE)
    .filter((F.col("model_name") == MODEL_NAME) & F.col("accepted"))
    .orderBy(F.col("created_at").desc())
    .limit(1)
    .collect()
)
if not candidate_rows:
    raise RuntimeError("No accepted candidate is available for promotion.")

candidate = candidate_rows[0]
client = MlflowClient()
previous_version = None
try:
    previous_version = client.get_model_version_by_alias(MODEL_NAME, cfg.model_alias).version
except Exception:
    previous_version = None

client.set_registered_model_alias(MODEL_NAME, cfg.model_alias, candidate.model_version)
client.set_model_version_tag(
    MODEL_NAME, candidate.model_version, "promotion_status", "active"
)
client.set_model_version_tag(
    MODEL_NAME, candidate.model_version, "promoted_at", datetime.now(timezone.utc).isoformat()
)

record = Row(
    model_name=MODEL_NAME,
    alias=cfg.model_alias,
    promoted_version=str(candidate.model_version),
    previous_version=str(previous_version) if previous_version else "",
    run_id=candidate.run_id,
    promoted_at=datetime.now(timezone.utc),
    rollback_target=str(previous_version) if previous_version else "",
)
spark.createDataFrame([record]).write.mode("append").saveAsTable(PROMOTION_TABLE)
