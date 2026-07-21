# Generated Sample Data and Outputs

This directory provides a compact, public-safe snapshot of the credential-free pipeline so the inputs and outputs can be inspected without downloading the full generated dataset.

## What is included

### Generated source samples

| File | Grain | Contents |
|---|---|---|
| `sample_data/members_sample.csv` | one row per member | tier, market, and tenure inputs without names, emails, or phone numbers |
| `sample_data/reservations_sample.csv` | one row per reservation | booking and stay dates, resort linkage, status, nights, points, and revenue |
| `sample_data/points_transactions_sample.csv` | one row per points transaction | earning, redemption, expiration, and adjustment activity |
| `sample_data/tour_events_sample.csv` | one row per tour event | package-to-prospect linkage, tour status, date, and market |
| `sample_data/labor_shifts_sample.csv` | one row per employee shift | resort-day labor hours and generated payroll cost |

### Generated platform outputs

| File | Grain | Contents |
|---|---|---|
| `sample_outputs/member_month_features_sample.csv` | member + as-of month | reusable point-in-time features, including average booking lead time, and the generated validation label |
| `sample_outputs/waterfall_forecast_sample.csv` | resort + forecast week + run | actuals, predictions, error, model alias, and scoring metadata |
| `sample_outputs/data_quality_results.csv` | table + quality check | schema, key, null, and referential-integrity outcomes |
| `sample_outputs/validation_summary.json` | one validation run | source volumes, model metrics, monitoring status, and acceptance gates |

## Reproduce the samples

```bash
python scripts/run_all.py
python scripts/export_examples.py
```

The exporter removes volatile timestamps and direct synthetic contact fields, sorts by stable business keys, and writes a deterministic sample pack. GitHub Actions regenerates the files and fails when the committed examples drift from the current pipeline.

## Public-safety boundary

All values are generated. The sample pack contains no real customer records, employee records, production credentials, proprietary source mappings, or confidential architecture.
