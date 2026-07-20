import mlflow
from pyspark.sql import functions as F

from common import parse_runtime_args, table

cfg = parse_runtime_args(include_model_alias=True)
MODEL_NAME = table(cfg.catalog, "models", "waterfall_forecast_model")
MODEL_URI = f"models:/{MODEL_NAME}@{cfg.model_alias}"
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

features = spark.table(table(cfg.catalog, "features", "waterfall_resort_week_features"))
score_udf = mlflow.pyfunc.spark_udf(spark, MODEL_URI, result_type="double")

scored = (
    features.withColumn("prediction", score_udf(*[F.col(c) for c in FEATURES]))
    .withColumn("model_alias", F.lit(cfg.model_alias))
    .withColumn("model_uri", F.lit(MODEL_URI))
    .withColumn("scored_at", F.current_timestamp())
)

(
    scored.write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(table(cfg.catalog, "gold", "waterfall_forecast_resort_week"))
)
