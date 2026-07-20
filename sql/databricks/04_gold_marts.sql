-- Required notebook parameter: catalog
USE CATALOG IDENTIFIER(:catalog);

CREATE OR REPLACE TABLE gold.resort_monthly_performance
USING DELTA
CLUSTER BY (resort_id, month_start) AS
WITH months AS (
  SELECT explode(sequence(DATE '2024-01-01', CAST(date_trunc('MONTH', current_date()) AS DATE), INTERVAL 1 MONTH)) AS month_start
),
resort_months AS (
  SELECT r.resort_id, r.resort_name, r.market, r.capacity_units, m.month_start
  FROM silver.resorts r CROSS JOIN months m
),
stays AS (
  SELECT resort_id, CAST(date_trunc('MONTH', check_in_date) AS DATE) AS month_start,
         reservation_id, member_id, room_nights, net_room_revenue, points_redeemed
  FROM silver.resort_stays
  WHERE stay_status IN ('BOOKED','IN_HOUSE','COMPLETED')
)
SELECT rm.resort_id, rm.resort_name, rm.market, rm.month_start,
  COUNT(DISTINCT s.reservation_id) AS reservation_count,
  COUNT(DISTINCT s.member_id) AS unique_members,
  COALESCE(SUM(s.room_nights),0) AS room_nights,
  COALESCE(SUM(s.net_room_revenue),0) AS net_room_revenue,
  COALESCE(SUM(s.points_redeemed),0) AS points_redeemed,
  COALESCE(SUM(s.net_room_revenue),0) / NULLIF(SUM(s.room_nights),0) AS adr,
  COALESCE(SUM(s.room_nights),0) / NULLIF(rm.capacity_units * day(last_day(rm.month_start)),0) AS occupancy_proxy
FROM resort_months rm
LEFT JOIN stays s ON rm.resort_id = s.resort_id AND rm.month_start = s.month_start
GROUP BY ALL;

CREATE OR REPLACE TABLE gold.campaign_tour_sales_attribution USING DELTA AS
WITH package_grain AS (
  SELECT * FROM silver.vacation_packages
  QUALIFY row_number() OVER (PARTITION BY package_id ORDER BY updated_at DESC) = 1
),
tour_grain AS (
  SELECT package_id, prospect_id, COUNT(DISTINCT tour_id) AS tours_scheduled,
    MAX(CASE WHEN tour_status = 'SHOW' THEN 1 ELSE 0 END) AS tours_showed
  FROM silver.tour_events GROUP BY package_id, prospect_id
),
contract_grain AS (
  SELECT package_id, prospect_id,
    MAX(CASE WHEN contract_status = 'SIGNED' THEN 1 ELSE 0 END) AS contracts_signed,
    SUM(CASE WHEN contract_status = 'SIGNED' THEN net_contract_value ELSE 0 END) AS net_contract_value
  FROM silver.sales_contracts GROUP BY package_id, prospect_id
)
SELECT p.campaign_id, p.lead_channel, p.market,
  CAST(date_trunc('MONTH', p.package_sale_date) AS DATE) AS month_start,
  COUNT(DISTINCT p.package_id) AS packages_sold,
  SUM(COALESCE(t.tours_scheduled,0)) AS tours_scheduled,
  SUM(COALESCE(t.tours_showed,0)) AS tours_showed,
  SUM(COALESCE(c.contracts_signed,0)) AS contracts_signed,
  SUM(COALESCE(c.net_contract_value,0)) AS net_contract_value,
  SUM(COALESCE(t.tours_showed,0)) / NULLIF(SUM(COALESCE(t.tours_scheduled,0)),0) AS tour_show_rate,
  SUM(COALESCE(c.contracts_signed,0)) / NULLIF(SUM(COALESCE(t.tours_showed,0)),0) AS show_to_contract_rate
FROM package_grain p
LEFT JOIN tour_grain t USING (package_id, prospect_id)
LEFT JOIN contract_grain c USING (package_id, prospect_id)
GROUP BY ALL;

CREATE OR REPLACE TABLE gold.member_points_utilization USING DELTA AS
SELECT member_id, CAST(date_trunc('MONTH', transaction_date) AS DATE) AS month_start,
  SUM(CASE WHEN transaction_type = 'EARN' THEN points_amount ELSE 0 END) AS points_earned,
  SUM(CASE WHEN transaction_type = 'REDEEM' THEN ABS(points_amount) ELSE 0 END) AS points_redeemed,
  SUM(CASE WHEN transaction_type = 'EXPIRE' THEN ABS(points_amount) ELSE 0 END) AS points_expired,
  SUM(CASE WHEN transaction_type = 'REDEEM' THEN ABS(points_amount) ELSE 0 END)
    / NULLIF(SUM(CASE WHEN transaction_type = 'EARN' THEN points_amount ELSE 0 END), 0) AS utilization_rate
FROM silver.points_transactions
GROUP BY member_id, CAST(date_trunc('MONTH', transaction_date) AS DATE);

CREATE OR REPLACE TABLE gold.resort_labor_efficiency USING DELTA AS
WITH labor AS (
  SELECT resort_id, work_date, SUM(labor_hours) AS labor_hours, SUM(payroll_cost) AS payroll_cost
  FROM silver.labor_shifts GROUP BY resort_id, work_date
),
stays AS (
  SELECT resort_id, check_in_date AS work_date, SUM(room_nights) AS occupied_room_nights,
         SUM(net_room_revenue) AS net_room_revenue
  FROM silver.resort_stays
  WHERE stay_status IN ('BOOKED','IN_HOUSE','COMPLETED')
  GROUP BY resort_id, check_in_date
)
SELECT l.resort_id, l.work_date, l.labor_hours, l.payroll_cost,
  COALESCE(s.occupied_room_nights, 0) AS occupied_room_nights,
  COALESCE(s.net_room_revenue, 0) AS net_room_revenue,
  l.payroll_cost / NULLIF(s.occupied_room_nights, 0) AS payroll_cost_per_occupied_room_night,
  s.net_room_revenue / NULLIF(l.labor_hours, 0) AS revenue_per_labor_hour
FROM labor l LEFT JOIN stays s USING (resort_id, work_date);

CREATE OR REPLACE TABLE semantic.metric_layer USING DELTA AS
SELECT * FROM VALUES
  ('reservation_count', 'COUNT DISTINCT reservation_id', 'gold.resort_monthly_performance', 'resort + month'),
  ('occupancy_proxy', 'room_nights / available_unit_nights', 'gold.resort_monthly_performance', 'resort + month'),
  ('show_to_contract_rate', 'contracts_signed / tours_showed', 'gold.campaign_tour_sales_attribution', 'campaign + channel + market + month'),
  ('points_utilization_rate', 'points_redeemed / points_earned', 'gold.member_points_utilization', 'member + month'),
  ('revenue_per_labor_hour', 'net_room_revenue / labor_hours', 'gold.resort_labor_efficiency', 'resort + business date')
AS metrics(metric_name, metric_definition, source_product, declared_grain);
