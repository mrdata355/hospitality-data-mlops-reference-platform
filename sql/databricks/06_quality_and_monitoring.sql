-- Required notebook parameter: catalog
USE CATALOG IDENTIFIER(:catalog);

CREATE TABLE IF NOT EXISTS ops.data_quality_results (
  pipeline_name STRING,
  table_name STRING,
  check_name STRING,
  status STRING,
  observed_value DOUBLE,
  threshold_value DOUBLE,
  details STRING,
  checked_at TIMESTAMP
) USING DELTA;

INSERT INTO ops.data_quality_results
SELECT 'member_features' AS pipeline_name,
  concat(:catalog, '.features.member_month_features') AS table_name,
  'duplicate_grain' AS check_name,
  CASE WHEN COUNT(*) - COUNT(DISTINCT member_id, as_of_month) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  COUNT(*) - COUNT(DISTINCT member_id, as_of_month) AS observed_value,
  0 AS threshold_value,
  'Expected one row per member and as_of_month' AS details,
  current_timestamp() AS checked_at
FROM features.member_month_features;

CREATE OR REPLACE TABLE ops.waterfall_forecast_accuracy USING DELTA AS
SELECT model_uri AS model_name,
  model_alias AS model_version_or_alias,
  week_start AS forecast_week_start,
  1 AS horizon_weeks,
  COUNT(*) AS forecast_count,
  AVG(ABS(arrivals - prediction)) AS mae,
  SUM(ABS(arrivals - prediction)) / NULLIF(SUM(ABS(arrivals)),0) AS wape,
  AVG(prediction - arrivals) AS forecast_bias,
  current_timestamp() AS calculated_at
FROM gold.waterfall_forecast_resort_week
WHERE arrivals IS NOT NULL
GROUP BY model_uri, model_alias, week_start;
