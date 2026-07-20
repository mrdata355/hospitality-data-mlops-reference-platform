from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from mlflow import MlflowClient
from pyspark.sql import Row, functions as F, types as T

from common import table

parser = argparse.ArgumentParser()
parser.add_argument(
    "--catalog", default=os.getenv("PLATFORM_CATALOG", "hospitality_data_platform_dev")
)
parser.add_argument("--model-alias", default=os.getenv("MODEL_ALIAS", "Champion"))
parser.add_argument(
    "--to-version",
    default="",
    help="Explicit model version. When omitted, use the latest recorded rollback target.",
)
args = parser.parse_args()

model_name = table(args.catalog, "models", "waterfall_forecast_model")
promotion_table = table(args.catalog, "ops", "model_promotion_history")
rollback_table = table(args.catalog, "ops", "model_rollback_history")

target_version = args.to_version.strip()
if not target_version:
    rows = (
        spark.table(promotion_table)
        .filter(
            (F.col("model_name") == model_name)
            & (F.col("alias") == args.model_alias)
            & F.col("rollback_target").isNotNull()
            & (F.length(F.col("rollback_target")) > 0)
        )
        .orderBy(F.col("promoted_at").desc())
        .limit(1)
        .collect()
    )
    if not rows:
        raise RuntimeError("No recorded rollback target is available.")
    target_version = rows[0].rollback_target

client = MlflowClient()
current_version = None
try:
    current_version = client.get_model_version_by_alias(
        model_name, args.model_alias
    ).version
except Exception:
    current_version = ""

client.set_registered_model_alias(model_name, args.model_alias, target_version)
client.set_model_version_tag(
    model_name, target_version, "rollback_activated_at", datetime.now(timezone.utc).isoformat()
)

schema = T.StructType(
    [
        T.StructField("model_name", T.StringType(), False),
        T.StructField("alias", T.StringType(), False),
        T.StructField("from_version", T.StringType(), True),
        T.StructField("to_version", T.StringType(), False),
        T.StructField("rolled_back_at", T.TimestampType(), False),
    ]
)
record = Row(
    model_name=model_name,
    alias=args.model_alias,
    from_version=str(current_version or ""),
    to_version=str(target_version),
    rolled_back_at=datetime.now(timezone.utc),
)
spark.createDataFrame([record], schema=schema).write.mode("append").saveAsTable(
    rollback_table
)
