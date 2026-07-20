-- Required notebook parameter: catalog
USE CATALOG IDENTIFIER(:catalog);

MERGE INTO silver.reservations AS target
USING (
  SELECT * EXCEPT(rn)
  FROM (
    SELECT
      reservation_id,
      member_id,
      resort_id,
      CAST(booking_date AS DATE) AS booking_date,
      CAST(check_in_date AS DATE) AS check_in_date,
      CAST(check_out_date AS DATE) AS check_out_date,
      UPPER(reservation_status) AS reservation_status,
      CAST(room_nights AS INT) AS room_nights,
      CAST(points_redeemed AS BIGINT) AS points_redeemed,
      CAST(net_room_revenue AS DECIMAL(18,2)) AS net_room_revenue,
      updated_at,
      _ingested_at,
      ROW_NUMBER() OVER (PARTITION BY reservation_id ORDER BY updated_at DESC, _ingested_at DESC) AS rn
    FROM bronze.reservations_raw
    WHERE reservation_id IS NOT NULL
      AND member_id IS NOT NULL
      AND resort_id IS NOT NULL
  )
  WHERE rn = 1
) AS source
ON target.reservation_id = source.reservation_id
WHEN MATCHED AND source.updated_at >= target.updated_at THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
