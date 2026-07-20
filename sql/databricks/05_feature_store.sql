-- Required notebook parameters: catalog, as_of_month (YYYY-MM-DD)
USE CATALOG IDENTIFIER(:catalog);

CREATE OR REPLACE TABLE features.member_month_features
USING DELTA
CLUSTER BY (member_id, as_of_month) AS
WITH base AS (
  SELECT m.member_id, CAST(:as_of_month AS DATE) AS as_of_month,
         m.member_tier, m.home_market,
         CAST(months_between(CAST(:as_of_month AS DATE), m.member_since_date) AS INT) AS tenure_months
  FROM silver.members m
),
points_12m AS (
  SELECT b.member_id, b.as_of_month,
    SUM(CASE WHEN p.transaction_type = 'EARN' THEN p.points_amount ELSE 0 END) AS points_earned_12m,
    SUM(CASE WHEN p.transaction_type = 'REDEEM' THEN ABS(p.points_amount) ELSE 0 END) AS points_redeemed_12m,
    SUM(CASE WHEN p.transaction_type = 'EXPIRE' THEN ABS(p.points_amount) ELSE 0 END) AS points_expired_12m
  FROM base b
  LEFT JOIN silver.points_transactions p ON b.member_id = p.member_id
   AND p.transaction_date >= add_months(b.as_of_month, -12)
   AND p.transaction_date < b.as_of_month
  GROUP BY b.member_id, b.as_of_month
),
stays_12m AS (
  SELECT b.member_id, b.as_of_month,
    COUNT(DISTINCT s.stay_id) AS stays_12m,
    SUM(s.room_nights) AS room_nights_12m,
    SUM(s.net_room_revenue) AS net_room_revenue_12m,
    AVG(GREATEST(datediff(s.check_in_date, s.booking_date), 0)) AS avg_booking_lead_days_12m,
    MAX(s.booking_date) AS last_booking_date
  FROM base b
  LEFT JOIN silver.resort_stays s ON b.member_id = s.member_id
   AND s.check_in_date >= add_months(b.as_of_month, -12)
   AND s.check_in_date < b.as_of_month
   AND s.stay_status IN ('BOOKED','IN_HOUSE','COMPLETED')
  GROUP BY b.member_id, b.as_of_month
),
service_90d AS (
  SELECT b.member_id, b.as_of_month,
    COUNT(DISTINCT c.case_id) AS service_cases_90d,
    SUM(CASE WHEN c.case_priority = 'ESCALATED' THEN 1 ELSE 0 END) AS escalated_cases_90d,
    AVG(c.resolution_hours) AS avg_resolution_hours_90d
  FROM base b
  LEFT JOIN silver.service_cases c ON b.member_id = c.member_id
   AND c.case_created_at >= date_sub(b.as_of_month, 90)
   AND c.case_created_at < b.as_of_month
  GROUP BY b.member_id, b.as_of_month
)
SELECT b.*,
  COALESCE(p.points_earned_12m,0) AS points_earned_12m,
  COALESCE(p.points_redeemed_12m,0) AS points_redeemed_12m,
  COALESCE(p.points_expired_12m,0) AS points_expired_12m,
  COALESCE(s.stays_12m,0) AS stays_12m,
  COALESCE(s.room_nights_12m,0) AS room_nights_12m,
  COALESCE(s.net_room_revenue_12m,0) AS net_room_revenue_12m,
  COALESCE(s.avg_booking_lead_days_12m,0) AS avg_booking_lead_days_12m,
  COALESCE(c.service_cases_90d,0) AS service_cases_90d,
  COALESCE(c.escalated_cases_90d,0) AS escalated_cases_90d,
  COALESCE(c.avg_resolution_hours_90d,0) AS avg_resolution_hours_90d,
  COALESCE(datediff(b.as_of_month, s.last_booking_date),9999) AS days_since_last_booking,
  COALESCE(p.points_redeemed_12m,0) / NULLIF(COALESCE(p.points_earned_12m,0),0) AS points_utilization_rate,
  COALESCE(p.points_expired_12m,0) / NULLIF(COALESCE(p.points_earned_12m,0),0) AS expired_share,
  current_timestamp() AS feature_created_at
FROM base b
LEFT JOIN points_12m p USING (member_id, as_of_month)
LEFT JOIN stays_12m s USING (member_id, as_of_month)
LEFT JOIN service_90d c USING (member_id, as_of_month);
