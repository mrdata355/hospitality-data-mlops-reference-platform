from __future__ import annotations

import argparse
import json
import math
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx

PAYLOAD = {
    "tenure_months": 48,
    "points_earned_12m": 42000,
    "points_redeemed_12m": 16000,
    "points_expired_12m": 3000,
    "points_utilization_rate": 0.38,
    "expired_share": 0.07,
    "stays_12m": 3,
    "room_nights_12m": 11,
    "net_room_revenue_12m": 2800,
    "avg_booking_lead_days_12m": 64,
    "service_cases_90d": 1,
    "escalated_cases_90d": 0,
    "avg_resolution_hours_90d": 14,
    "days_since_last_booking": 88,
    "member_tier": "Elite",
    "home_market": "Orlando",
}

_thread_state = threading.local()


def _client(timeout_seconds: float) -> httpx.Client:
    client = getattr(_thread_state, "client", None)
    if client is None:
        client = httpx.Client(timeout=timeout_seconds)
        _thread_state.client = client
    return client


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _request(base_url: str, timeout_seconds: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = _client(timeout_seconds).post(
            f"{base_url.rstrip('/')}/score/member-churn", json=PAYLOAD
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        contract_ok = False
        if response.status_code == 200:
            body = response.json()
            contract_ok = {
                "churn_probability",
                "risk_band",
                "model_alias",
                "scored_at",
                "request_id",
            }.issubset(body)
        return {
            "latency_ms": elapsed_ms,
            "status_code": response.status_code,
            "contract_ok": contract_ok,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "latency_ms": (time.perf_counter() - started) * 1000,
            "status_code": None,
            "contract_ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_benchmark(
    *,
    base_url: str,
    requests: int,
    concurrency: int,
    warmup: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    if requests < 1 or concurrency < 1 or warmup < 0:
        raise ValueError("requests and concurrency must be positive; warmup cannot be negative.")

    for _ in range(warmup):
        result = _request(base_url, timeout_seconds)
        if result["status_code"] != 200 or not result["contract_ok"]:
            raise RuntimeError(f"Warmup request failed: {result}")

    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_request, base_url, timeout_seconds) for _ in range(requests)]
        for future in as_completed(futures):
            results.append(future.result())
    duration_seconds = time.perf_counter() - started

    successful = [result for result in results if result["status_code"] == 200]
    latencies = [float(result["latency_ms"]) for result in successful]
    contract_failures = sum(not result["contract_ok"] for result in successful)
    errors = [result for result in results if result["status_code"] != 200]
    status_counts: dict[str, int] = {}
    for result in results:
        key = str(result["status_code"] or "exception")
        status_counts[key] = status_counts.get(key, 0) + 1

    return {
        "workload": {
            "requests": requests,
            "concurrency": concurrency,
            "warmup_requests": warmup,
            "timeout_seconds": timeout_seconds,
        },
        "results": {
            "duration_seconds": duration_seconds,
            "throughput_requests_per_second": requests / max(duration_seconds, 0.001),
            "successful_requests": len(successful),
            "failed_requests": len(errors),
            "error_rate": len(errors) / requests,
            "contract_failures": contract_failures,
            "status_counts": status_counts,
            "latency_ms": {
                "mean": statistics.fmean(latencies) if latencies else math.nan,
                "p50": _percentile(latencies, 0.50),
                "p95": _percentile(latencies, 0.95),
                "p99": _percentile(latencies, 0.99),
                "max": max(latencies) if latencies else math.nan,
            },
        },
        "errors": [result["error"] for result in errors if result["error"]][:10],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the running member-risk API.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-p95-ms", type=float, default=1000.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_benchmark(
        base_url=args.base_url,
        requests=args.requests,
        concurrency=args.concurrency,
        warmup=args.warmup,
        timeout_seconds=args.timeout_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    results = report["results"]
    if results["failed_requests"]:
        raise RuntimeError(f"Benchmark recorded failed requests: {results}")
    if results["contract_failures"]:
        raise RuntimeError(f"Benchmark recorded response-contract failures: {results}")
    if results["latency_ms"]["p95"] > args.max_p95_ms:
        raise RuntimeError(
            f"p95 latency {results['latency_ms']['p95']:.2f} ms exceeded "
            f"the {args.max_p95_ms:.2f} ms CI ceiling."
        )


if __name__ == "__main__":
    main()
