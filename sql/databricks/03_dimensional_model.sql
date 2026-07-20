-- Required notebook parameter: catalog
USE CATALOG IDENTIFIER(:catalog);

CREATE OR REPLACE TABLE gold.dim_resort USING DELTA AS
SELECT xxhash64(resort_id) AS resort_key, resort_id, resort_name, market, region,
       capacity_units, property_type, active_flag
FROM silver.resorts;

CREATE OR REPLACE TABLE gold.dim_member USING DELTA AS
SELECT xxhash64(member_id) AS member_key, member_id, member_tier, home_market,
       member_since_date, active_flag
FROM silver.members;

CREATE OR REPLACE TABLE gold.dim_campaign USING DELTA AS
SELECT xxhash64(campaign_id) AS campaign_key, campaign_id, campaign_name, channel,
       target_market, start_date, end_date, budget
FROM silver.campaigns;

CREATE OR REPLACE TABLE gold.dim_date USING DELTA AS
SELECT CAST(date_format(calendar_date, 'yyyyMMdd') AS INT) AS date_key,
       calendar_date AS full_date, year(calendar_date) AS calendar_year,
       quarter(calendar_date) AS calendar_quarter, month(calendar_date) AS calendar_month,
       weekofyear(calendar_date) AS week_of_year, dayofweek(calendar_date) IN (1, 7) AS weekend_flag
FROM (SELECT explode(sequence(DATE '2024-01-01', DATE '2027-12-31', INTERVAL 1 DAY)) AS calendar_date);

CREATE OR REPLACE TABLE gold.fact_reservation USING DELTA AS
SELECT r.reservation_id, m.member_key, d.resort_key,
       CAST(date_format(r.booking_date, 'yyyyMMdd') AS INT) AS booking_date_key,
       CAST(date_format(r.check_in_date, 'yyyyMMdd') AS INT) AS check_in_date_key,
       CAST(date_format(r.check_out_date, 'yyyyMMdd') AS INT) AS check_out_date_key,
       r.reservation_status, r.room_nights, r.points_redeemed, r.net_room_revenue
FROM silver.reservations r
JOIN gold.dim_member m ON r.member_id = m.member_id
JOIN gold.dim_resort d ON r.resort_id = d.resort_id;

CREATE OR REPLACE TABLE gold.fact_stay USING DELTA AS
SELECT s.stay_id, s.reservation_id, m.member_key, r.resort_key,
       CAST(date_format(s.check_in_date, 'yyyyMMdd') AS INT) AS check_in_date_key,
       s.stay_status, s.room_nights, s.points_redeemed, s.net_room_revenue
FROM silver.resort_stays s
JOIN gold.dim_member m ON s.member_id = m.member_id
JOIN gold.dim_resort r ON s.resort_id = r.resort_id;

CREATE OR REPLACE TABLE gold.fact_points_transaction USING DELTA AS
SELECT p.transaction_id, m.member_key,
       CAST(date_format(p.transaction_date, 'yyyyMMdd') AS INT) AS transaction_date_key,
       p.transaction_type, p.points_amount
FROM silver.points_transactions p
JOIN gold.dim_member m ON p.member_id = m.member_id;

CREATE OR REPLACE TABLE gold.fact_tour_event USING DELTA AS
SELECT tour_id, package_id, prospect_id,
       CAST(date_format(tour_date, 'yyyyMMdd') AS INT) AS tour_date_key,
       tour_status, market
FROM silver.tour_events;

CREATE OR REPLACE TABLE gold.fact_sales_contract USING DELTA AS
SELECT contract_id, package_id, prospect_id,
       CAST(date_format(contract_date, 'yyyyMMdd') AS INT) AS contract_date_key,
       contract_status, net_contract_value
FROM silver.sales_contracts;

CREATE OR REPLACE TABLE gold.fact_service_case USING DELTA AS
SELECT c.case_id, m.member_key,
       CAST(date_format(c.case_created_at, 'yyyyMMdd') AS INT) AS case_date_key,
       c.case_priority, c.resolution_hours, c.case_status
FROM silver.service_cases c
JOIN gold.dim_member m ON c.member_id = m.member_id;

CREATE OR REPLACE TABLE gold.fact_labor_shift USING DELTA AS
SELECT l.shift_id, r.resort_key, l.employee_id,
       CAST(date_format(l.work_date, 'yyyyMMdd') AS INT) AS work_date_key,
       l.labor_hours, l.payroll_cost
FROM silver.labor_shifts l
JOIN gold.dim_resort r ON l.resort_id = r.resort_id;

CREATE OR REPLACE TABLE gold.fact_marketing_touch USING DELTA AS
SELECT e.touch_id, e.prospect_id, e.member_id, c.campaign_key,
       CAST(date_format(e.touch_time, 'yyyyMMdd') AS INT) AS touch_date_key,
       e.channel, e.market
FROM silver.marketing_events e
JOIN gold.dim_campaign c ON e.campaign_id = c.campaign_id;
