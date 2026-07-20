# API Load and Contract Validation

This directory contains a Locust workload for exercising the member-risk FastAPI service under concurrent traffic.

The load test is intended to validate request behavior, response contracts, readiness, liveness, and scaling assumptions in a controlled environment. It does not claim a production throughput limit until a measured run is executed against authorized infrastructure and the results are retained.

## Workload profile

The `ScoringUser` workload uses weighted tasks:

| Request | Weight | Purpose |
|---|---:|---|
| `POST /score/member-churn` | 8 | exercises model inference and validates the returned risk-band contract |
| `GET /ready` | 1 | verifies that the model remains loaded and the instance remains eligible for traffic |
| `GET /health` | 1 | verifies process responsiveness |

Each simulated user waits between `0.1` and `0.5` seconds between tasks. Scoring requests include a unique `x-request-id` so request tracing behavior is exercised.

## Payload coverage

The representative generated payload includes:

- member tenure
- points earned, redeemed, and expired
- utilization and expiration share
- stays, room nights, and revenue
- service cases and escalations
- resolution duration
- booking recency
- tier and home market

The test marks a scoring request as failed when:

- the service returns a non-200 status
- the response does not contain a valid `LOW`, `MEDIUM`, or `HIGH` risk band
- the service is not ready during user startup

## Start the service

Generate the local model and start the API:

```bash
make run
make api
```

The API should be available at:

```text
http://localhost:8080
```

## Interactive Locust run

Install development tools:

```bash
pip install -r requirements-dev.txt
```

Start Locust:

```bash
make loadtest
```

Open:

```text
http://localhost:8089
```

## Headless examples

### Local smoke load

```bash
locust \
  -f loadtest/locustfile.py \
  --host http://localhost:8080 \
  --headless \
  --users 10 \
  --spawn-rate 2 \
  --run-time 1m
```

### Staging characterization run

```bash
locust \
  -f loadtest/locustfile.py \
  --host https://REPLACE_WITH_STAGING_ENDPOINT \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --csv loadtest/results/staging
```

## Proposed staging gates

These are release targets to validate, not preclaimed measured results:

| Signal | Initial gate |
|---|---:|
| Failed request rate | `< 1%` |
| `POST /score/member-churn` p95 | `< 300 ms`, excluding external network edge |
| `POST /score/member-churn` p99 | `< 750 ms` |
| Readiness failures during steady state | `0` |
| Invalid response contracts | `0` |
| Uncontrolled pod restarts | `0` |

Thresholds should be revised from actual staging measurements and business latency requirements.

## Capacity-testing progression

A controlled performance program should progress through:

1. **Smoke:** confirm the workload and service contract.
2. **Baseline:** measure one pod at low concurrency.
3. **Step load:** increase concurrent users in defined stages.
4. **Autoscaling:** verify HPA activation, scale-up time, and stabilization.
5. **Soak:** hold expected traffic long enough to detect memory growth and latency drift.
6. **Failure injection:** terminate pods or remove model access and confirm graceful recovery.
7. **Rollback:** restore the prior application image or MLflow alias and re-run smoke validation.

## Metrics to retain

For an authorized staging run, preserve:

- requests per second
- p50, p95, and p99 latency by endpoint
- error and timeout rates
- pod count over time
- CPU and memory utilization
- model load time
- restart count
- HPA decisions
- model version and application image digest
- test configuration and source commit

## Relationship to Kubernetes sizing

The Kubernetes HPA currently provides a production-style starting range of 3 to 30 replicas. Load-test evidence should determine:

- realistic requests per pod
- CPU and memory requests
- scale-up thresholds
- minimum replicas needed for availability and baseline traffic
- maximum replicas allowed by cost and downstream capacity

## Safety boundary

Use generated feature payloads only. Do not include real customer records, production tokens, internal endpoint credentials, or proprietary request data in Locust source, CSV outputs, screenshots, or logs.
