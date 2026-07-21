# Model Card

## Scope

This document covers the generated-data member-risk classifier and resort-week arrivals forecaster included in the hospitality reference platform.

Both models exist to validate data contracts, temporal feature construction, acceptance gates, registry controls, batch/API scoring, monitoring, and rollback. They are not approved for customer treatment, staffing, pricing, credit, eligibility, or other consequential decisions.

## Member-risk classifier

### Intended system use

- Validate the member-month feature contract.
- Exercise batch scoring and the FastAPI response contract.
- Demonstrate model artifact transfer into a clean serving build job.
- Produce deterministic risk-band outputs for testing monitoring and API controls.

### Model and inputs

The local path uses a class-weighted logistic regression pipeline with median imputation, numeric scaling, and one-hot encoding. Inputs include tenure, points behavior, stays, room nights, revenue, booking lead time, service activity, booking recency, member tier, and home market.

### Label construction

The churn label is generated deterministically from a synthetic risk equation and a stable member identifier hash. Several terms in that equation are also included in the training feature family. The reported ROC AUC therefore confirms that the pipeline can learn, serialize, reload, score, and validate a known signal. It does not estimate performance on real members.

### Current deterministic result

- ROC AUC: approximately `0.810`
- Decision threshold: `0.50`
- API risk bands: Low below `0.35`, Medium from `0.35` to below `0.65`, High at or above `0.65`

The threshold and risk bands are operational demonstration settings. They have not been optimized against retention cost, contact capacity, customer impact, or expected value.

## Resort-week arrivals forecaster

### Intended system use

- Validate leakage-safe resort-week lag and rolling-window features.
- Demonstrate chronological evaluation and seasonal-baseline comparison.
- Exercise MLflow candidate registration, evidence retention, alias promotion, batch scoring, monitoring, and rollback.

### Model and inputs

The local and managed reference paths use a random forest regressor with one-, four-, thirteen-, and fifty-two-week lags; shifted rolling means; campaign intensity; seasonality; capacity; resort identity; month; and quarter.

### Evaluation

The primary release gate uses a chronological holdout. A candidate must remain below the configured maximum WAPE and beat the fifty-two-week seasonal baseline before it can become `Champion`.

The repository also runs an expanding-window rolling-origin backtest across multiple later validation windows. That evidence reports aggregate, fold, and resort-level WAPE, baseline WAPE, forecast bias, and baseline win rate.

### Current deterministic result

- Holdout WAPE: approximately `0.249`
- Seasonal baseline WAPE: approximately `0.265`
- Holdout forecast bias: approximately `1.21` arrivals

These values validate the generated-data workflow and acceptance logic. They are not capacity or revenue forecasts for a real resort group.

## Data and leakage controls

- Feature windows end before the scoring cutoff.
- Rolling features are shifted before aggregation.
- Labels are excluded from declared model feature lists.
- Member-month and resort-week grains are tested for uniqueness.
- Chronological validation keeps training observations earlier than validation observations.
- The API validates field names, types, allowed member tiers, and nonnegative numeric inputs.

## Monitoring

The reference implementation records or exposes:

- Feature drift using PSI.
- Forecast WAPE and bias.
- Risk-score distribution and high-risk share.
- Request count, server errors, average latency, build version, and model alias.
- Running-container smoke and concurrent benchmark evidence.

## Known limitations

- All source records and outcomes are synthetic.
- The member label-generation process creates a learnable signal by design.
- The forecasting model does not currently produce probabilistic intervals.
- Holiday, weather, local-event, price, competitor, and macroeconomic signals are not included.
- Real-world subgroup performance and fairness have not been evaluated.
- Real concept drift, delayed labels, feedback loops, and intervention effects are not represented.
- The local member model uses a single generated as-of month rather than a long historical snapshot series.

## Requirements before real decision use

A real deployment would require approved source contracts, privacy review, historical outcome definitions, leakage review, business-value thresholding, subgroup analysis, human-oversight rules, production backtesting, model-risk approval, documented fallbacks, monitoring ownership, retraining policy, and rollback exercises.
