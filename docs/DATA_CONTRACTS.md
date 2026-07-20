# Data Contracts

## Contract standard

Every source and data product has an owner, declared grain, business key, required fields, type expectations, freshness target, null policy, accepted values, retention rule, and downstream consumers. Breaking changes require a versioned contract and coordinated release.

## Source contracts

| Entity | Business key | Event or effective field | Required fields | Freshness |
|---|---|---|---|---|
| members | `member_id` | `updated_at` | tier, home market, member since date | daily |
| resorts | `resort_id` | `updated_at` | market, region, capacity | daily |
| reservations | `reservation_id` | `updated_at` | member, resort, booking and stay dates, status | hourly or daily |
| points transactions | `transaction_id` | `transaction_date` | member, transaction type, amount | daily |
| vacation packages | `package_id` | `updated_at` | prospect, campaign, channel, market, sale date | daily |
| tour events | `tour_id` | `tour_date` | package, prospect, status, market | daily |
| sales contracts | `contract_id` | `contract_date` | package, prospect, status, value | daily |
| marketing events | `touch_id` | `touch_time` | prospect or member, campaign, channel, market | hourly or daily |
| service cases | `case_id` | `case_created_at` | member, priority, status | daily |
| labor shifts | `shift_id` | `work_date` | resort, employee, hours, payroll cost | daily |

## Validation rules

- Business keys must be present and unique after latest-record deduplication.
- Foreign keys must resolve to active conformed entities or enter quarantine.
- Status values are normalized to controlled enumerations.
- Event dates cannot exceed the ingestion date beyond the configured future-date tolerance.
- Monetary and quantity fields must remain within configured lower and upper bounds.
- Row counts are checked against trailing volume bands to detect missing or duplicated deliveries.
- Schema changes are rejected unless explicitly approved and versioned.

## Feature contracts

### `features.member_month_features`

**Grain:** one row per `member_id` and `as_of_month`.

**Point-in-time rule:** only events strictly earlier than `as_of_month` are eligible.

**Required feature groups:**

- member tenure, tier, and home market
- points earned, redeemed, expired, utilization, and expired share
- stay count, room nights, revenue, and booking recency
- service case count, escalations, and resolution duration

### `features.waterfall_resort_week_features`

**Grain:** one row per `resort_id` and `forecast_week_start`.

**Required feature groups:**

- 1-, 4-, 13-, and 52-week lags
- 4- and 13-week rolling means
- calendar seasonality and holiday indicators
- resort capacity and market
- campaign intensity known at scoring time

## Change policy

- Additive nullable columns are backward compatible.
- Type changes, column removals, key changes, and semantic changes are breaking.
- Breaking changes require a new contract version, parallel validation, consumer sign-off, and a retirement date for the previous version.
