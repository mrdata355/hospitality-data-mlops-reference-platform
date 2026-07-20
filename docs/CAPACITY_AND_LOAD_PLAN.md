# Capacity and Load Plan

## Offline workloads

Validate row volume, file count, partition count, shuffle bytes, spill, skew, runtime, retry count, and cost at 1x, 5x, and 10x expected daily volume. Backfills are tested separately because their concurrency and storage patterns differ from daily processing.

## Online workloads

Test warm and cold model load behavior, steady-state QPS, burst QPS, p50/p95/p99 latency, memory growth, error rate, and recovery during rolling deployment. The initial target is three replicas with scale-out to thirty, subject to cluster capacity and downstream registry/network limits.

## Exit criteria

- no contract violations or dropped records
- no unbounded memory growth
- no sustained CPU or memory saturation
- p95 latency within the approved SLO
- zero failed requests during rolling deployment
- acceptable cost per one thousand predictions
- rollback completes within the recovery objective
