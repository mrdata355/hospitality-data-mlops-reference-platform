from pyspark.sql import functions as F

from common import parse_runtime_args, table

cfg = parse_runtime_args(include_as_of_month=True)
AS_OF_MONTH = F.to_date(F.lit(cfg.as_of_month))

members = spark.table(table(cfg.catalog, "silver", "members"))
points = spark.table(table(cfg.catalog, "silver", "points_transactions"))
stays = spark.table(table(cfg.catalog, "silver", "resort_stays"))
service = spark.table(table(cfg.catalog, "silver", "service_cases"))

base = members.select(
    "member_id",
    "member_tier",
    "home_market",
    AS_OF_MONTH.alias("as_of_month"),
    F.floor(F.months_between(AS_OF_MONTH, "member_since_date")).alias("tenure_months"),
)

points_12m = (
    base.alias("b")
    .join(
        points.alias("p"),
        (F.col("b.member_id") == F.col("p.member_id"))
        & (F.col("p.transaction_date") >= F.add_months(F.col("b.as_of_month"), -12))
        & (F.col("p.transaction_date") < F.col("b.as_of_month")),
        "left",
    )
    .groupBy("b.member_id", "b.as_of_month")
    .agg(
        F.sum(
            F.when(F.col("p.transaction_type") == "EARN", F.col("p.points_amount")).otherwise(0)
        ).alias("points_earned_12m"),
        F.sum(
            F.when(
                F.col("p.transaction_type") == "REDEEM", F.abs(F.col("p.points_amount"))
            ).otherwise(0)
        ).alias("points_redeemed_12m"),
        F.sum(
            F.when(
                F.col("p.transaction_type") == "EXPIRE", F.abs(F.col("p.points_amount"))
            ).otherwise(0)
        ).alias("points_expired_12m"),
    )
)

stays_12m = (
    base.alias("b")
    .join(
        stays.alias("s"),
        (F.col("b.member_id") == F.col("s.member_id"))
        & (F.col("s.check_in_date") >= F.add_months(F.col("b.as_of_month"), -12))
        & (F.col("s.check_in_date") < F.col("b.as_of_month")),
        "left",
    )
    .groupBy("b.member_id", "b.as_of_month")
    .agg(
        F.countDistinct("s.stay_id").alias("stays_12m"),
        F.sum(F.coalesce(F.col("s.room_nights"), F.lit(0))).alias("room_nights_12m"),
        F.sum(F.coalesce(F.col("s.net_room_revenue"), F.lit(0.0))).alias(
            "net_room_revenue_12m"
        ),
        F.max("s.booking_date").alias("last_booking_date"),
    )
)

service_90d = (
    base.alias("b")
    .join(
        service.alias("c"),
        (F.col("b.member_id") == F.col("c.member_id"))
        & (F.col("c.case_created_at") >= F.date_sub(F.col("b.as_of_month"), 90))
        & (F.col("c.case_created_at") < F.col("b.as_of_month")),
        "left",
    )
    .groupBy("b.member_id", "b.as_of_month")
    .agg(
        F.countDistinct("c.case_id").alias("service_cases_90d"),
        F.sum(F.when(F.col("c.case_priority") == "ESCALATED", 1).otherwise(0)).alias(
            "escalated_cases_90d"
        ),
        F.avg("c.resolution_hours").alias("avg_resolution_hours_90d"),
    )
)

features = (
    base.join(points_12m, ["member_id", "as_of_month"], "left")
    .join(stays_12m, ["member_id", "as_of_month"], "left")
    .join(service_90d, ["member_id", "as_of_month"], "left")
    .fillna(0)
    .withColumn(
        "points_utilization_rate",
        F.when(F.col("points_earned_12m") > 0, F.col("points_redeemed_12m") / F.col("points_earned_12m")).otherwise(F.lit(0.0)),
    )
    .withColumn(
        "expired_share",
        F.when(F.col("points_earned_12m") > 0, F.col("points_expired_12m") / F.col("points_earned_12m")).otherwise(F.lit(0.0)),
    )
    .withColumn(
        "days_since_last_booking",
        F.coalesce(F.datediff(F.col("as_of_month"), F.col("last_booking_date")), F.lit(9999)),
    )
    .drop("last_booking_date")
)

(
    features.write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(table(cfg.catalog, "features", "member_month_features"))
)
