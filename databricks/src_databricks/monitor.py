from pyspark.sql import functions as F

from common import parse_runtime_args, table

cfg = parse_runtime_args()
forecast = spark.table(table(cfg.catalog, "gold", "waterfall_forecast_resort_week"))

denominator = F.greatest(F.sum(F.abs(F.col("arrivals"))), F.lit(1.0))
health = (
    forecast.agg(
        F.avg(F.abs(F.col("arrivals") - F.col("prediction"))).alias("mae"),
        (F.sum(F.abs(F.col("arrivals") - F.col("prediction"))) / denominator).alias(
            "wape"
        ),
        F.avg(F.col("prediction") - F.col("arrivals")).alias("forecast_bias"),
        F.count(F.lit(1)).alias("scored_rows"),
    )
    .withColumn("calculated_at", F.current_timestamp())
    .withColumn("catalog", F.lit(cfg.catalog))
)

health.write.mode("append").saveAsTable(table(cfg.catalog, "ops", "model_health"))
