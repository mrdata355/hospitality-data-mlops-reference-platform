# Data Dictionary

## dim_member

| Column | Type | Meaning |
|---|---|---|
| member_key | integer | Surrogate key |
| member_id | string | Stable business key |
| member_tier | string | Club tier |
| home_market | string | Home market |
| member_since_date | date | Membership start |
| active_flag | integer | Current active indicator |

## dim_resort

| Column | Type | Meaning |
|---|---|---|
| resort_key | integer | Surrogate key |
| resort_id | string | Stable resort key |
| resort_name | string | Resort name |
| market | string | Business market |
| region | string | Region |
| capacity_units | integer | Generated validation capacity |
| property_type | string | Resort property type |

## fact_stay

**Grain:** one row per stay.

| Column | Meaning |
|---|---|
| stay_id | Stay business key |
| reservation_id | Reservation business key |
| member_key | Member surrogate key |
| resort_key | Resort surrogate key |
| check_in_date_key | Integer date key |
| room_nights | Nights attached to the stay record |
| net_room_revenue | Generated validation net room revenue |
| points_redeemed | Points used for the stay |
| stay_status | BOOKED, IN_HOUSE, COMPLETED, or CANCELLED |

## features.member_month_features

**Grain:** one row per member per as-of month.

| Feature | Definition |
|---|---|
| tenure_months | Months from member start to as-of month |
| points_earned_12m | Earned points in the prior 12 months |
| points_redeemed_12m | Redeemed points in the prior 12 months |
| points_expired_12m | Expired points in the prior 12 months |
| points_utilization_rate | Redeemed divided by earned |
| stays_12m | Completed stays in the prior 12 months |
| room_nights_12m | Room nights in the prior 12 months |
| service_cases_90d | Cases in the prior 90 days |
| escalated_cases_90d | Escalated cases in the prior 90 days |
| days_since_last_booking | Days since latest booking before cutoff |
| churn_label | Generated future inactivity label; never used as a feature |

## features.waterfall_resort_week_features

**Grain:** one row per resort and forecast week.

| Feature | Definition |
|---|---|
| lag_1w | Arrivals one week earlier |
| lag_4w | Arrivals four weeks earlier |
| lag_13w | Arrivals thirteen weeks earlier |
| rolling_mean_4w | Mean arrivals over prior four weeks |
| rolling_mean_13w | Mean arrivals over prior thirteen weeks |
| campaign_intensity | Marketing touches in the resort market during the prior week |
| week_of_year | Calendar week |
| month | Calendar month |
| capacity_units | Resort capacity |
