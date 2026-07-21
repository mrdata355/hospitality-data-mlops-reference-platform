# Performance Validation

## Purpose

The serving benchmark verifies that the released container remains responsive under a small concurrent workload and continues to satisfy the scoring response contract. It is a regression gate, not a production-capacity claim.

## CI workload

After the restricted container passes readiness and the end-to-end scoring smoke test, CI executes:

```bash
python scripts/benchmark_serving.py \
  --base-url http://localhost:8080 \
  --requests 200 \
  --concurrency 16 \
  --warmup 20 \
  --max-p95-ms 1000 \
  --output artifacts/serving/ci-benchmark.json
```

The benchmark records:

- Total duration and achieved request throughput.
- Successful and failed request counts.
- HTTP status distribution and error rate.
- Response-contract failures.
- Mean, p50, p95, p99, and maximum latency.
- A bounded sample of request exceptions.

## CI acceptance conditions

The benchmark fails when:

- Any measured request fails.
- Any successful response violates the documented response contract.
- p95 latency exceeds the one-second CI regression ceiling.

The one-second ceiling is deliberately conservative for a shared hosted runner. It detects major regressions but does not define a production SLO.

## Evidence

Each CI run uploads the following short-retention evidence under the `serving-evidence` artifact:

- `ci-smoke.json`
- `ci-benchmark.json`
- `container-inspect.json`
- `container.log`

The application also exposes `/metrics`, `/version`, `/model-info`, `/health`, and `/ready` for release and runtime inspection.

## Production capacity boundary

A production authorization would require longer soak tests, representative payload distributions, multiple replica counts, autoscaling validation, downstream MLflow/network latency, failure injection, resource saturation tests, cost measurements, and p50/p95/p99 targets derived from the consuming business process.
