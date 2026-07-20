from pyspark.sql import Window
from pyspark.sql import functions as F

from common import parse_runtime_args, table

cfg = parse_runtime_args()

stays = spark.table(table(cfg.catalog, "silver", "resort_stays"))
resorts = spark.table(table(cfg.catalog, "silver", "resorts"))
marketing = spark.table(table(cfg.catalog, "silver", "marketing_events"))

weekly_arrivals = (
    stays.filter(F.col("stay_status") != "CANCELLED")
    .withColumn("week_start", F.to_date(F.date_trunc("week", F.col("check_in_date"))))
    .groupBy("resort_id", "week_start")
    .agg(F.countDistinct("stay_id").alias("arrivals"))
)

weekly_campaigns = (
    marketing.withColumn("week_start", F.to_date(F.date_trunc("week", F.col("touch_time"))))
    .groupBy("market", "week_start")
    .agg(F.countDistinct("touch_id").alias("campaign_intensity"))
)

base = (
    weekly_arrivals.join(
        resorts.select("resort_id", "market", "capacity_units"), "resort_id", "left"
    )
    .join(weekly_campaigns, ["market", "week_start"], "left")
    .fillna({"campaign_intensity": 0})
)

w = Window.partitionBy("resort_id").orderBy("week_start")
features = (
    base.withColumn("lag_1w", F.lag("arrivals", 1).over(w))
    .withColumn("lag_4w", F.lag("arrivals", 4).over(w))
    .withColumn("lag_13w", F.lag("arrivals", 13).over(w))
    .withColumn("lag_52w", F.lag("arrivals", 52).over(w))
    .withColumn("rolling_mean_4w", F.avg("arrivals").over(w.rowsBetween(-4, -1)))
    .withColumn("rolling_mean_13w", F.avg("arrivals").over(w.rowsBetween(-13, -1)))
    .withColumn("week_of_year", F.weekofyear("week_start"))
    .withColumn("month", F.month("week_start"))
    .withColumn("quarter", F.quarter("week_start"))
    .withColumn("season_sin", F.sin(F.lit(2.0 * 3.141592653589793) * F.col("week_of_year") / F.lit(52.0)))
    .withColumn("season_cos", F.cos(F.lit(2.0 * 3.141592653589793) * F.col("week_of_year") / F.lit(52.0)))
    .withColumn("resort_code", F.dense_rank().over(Window.orderBy("resort_id")) - 1)
    .dropna(subset=["lag_1w", "lag_4w", "lag_13w", "lag_52w", "rolling_mean_4w", "rolling_mean_13w"])
)

(
    features.write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(table(cfg.catalog, "features", "waterfall_resort_week_features"))
)
