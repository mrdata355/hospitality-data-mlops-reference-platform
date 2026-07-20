# Service Levels and Monitoring

## Service level objectives

| Capability | SLO | Measurement window | Alert threshold |
|---|---|---|---|
| daily pipeline completion | 99.5% successful scheduled runs | rolling 30 days | one failed critical run |
| Gold data freshness | published by 07:00 local business time | daily | 30 minutes late |
| feature freshness | completed before model scoring starts | each scoring cycle | missing or stale feature partition |
| batch scoring completion | 99.5% successful runs | rolling 30 days | one failed production run |
| online API availability | 99.9% | rolling 30 days | two consecutive failed probes |
| online p95 latency | under 300 ms excluding network edge | 15-minute window | over 300 ms for 3 windows |
| data quality pass rate | at least 99.0% non-quarantined rows | per batch | below threshold |
| model artifact load | 100% before readiness succeeds | each deployment | any load failure |

## Model performance objectives

| Model | Primary metric | Promotion gate | Production action threshold |
|---|---|---|---|
| member risk | ROC AUC | at least 0.75 on approved holdout | below 0.72 after labels mature |
| member risk | recall at operating threshold | business-approved minimum | 10% relative decline |
| resort-week forecast | WAPE | no worse than approved seasonal baseline | 15% relative degradation |
| resort-week forecast | bias | within approved market band | sustained directional bias |

## Monitored signals

- source and table freshness
- row counts and historical volume bands
- schema changes and rejected records
- null, uniqueness, and referential integrity rates
- workflow runtime, retries, and failed task keys
- model input drift, missingness, and cardinality changes
- prediction distribution and risk-band mix
- actual-versus-predicted error by resort, market, and horizon
- API request volume, p50/p95/p99 latency, error rate, and saturation
- cost by workspace, job, cluster policy, and model endpoint

## Severity levels

| Severity | Definition | Response target |
|---|---|---|
| SEV-1 | business-critical data or scoring unavailable with no safe fallback | acknowledge within 15 minutes |
| SEV-2 | major delay or degradation with partial workaround | acknowledge within 30 minutes |
| SEV-3 | isolated defect, non-critical data quality issue, or minor latency increase | acknowledge within 4 business hours |
| SEV-4 | documentation, backlog, or cosmetic issue | next planned work cycle |
