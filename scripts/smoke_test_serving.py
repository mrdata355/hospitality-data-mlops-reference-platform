from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCORE_PAYLOAD = {
    "tenure_months": 36,
    "points_earned_12m": 28000,
    "points_redeemed_12m": 8000,
    "points_expired_12m": 2500,
    "points_utilization_rate": 0.2857,
    "expired_share": 0.089,
    "stays_12m": 1,
    "room_nights_12m": 4,
    "net_room_revenue_12m": 1250,
    "avg_booking_lead_days_12m": 47.5,
    "service_cases_90d": 2,
    "escalated_cases_90d": 1,
    "avg_resolution_hours_90d": 52,
    "days_since_last_booking": 230,
    "member_tier": "Member",
    "home_market": "Orlando",
}


def request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> tuple[int, dict[str, Any], dict[str, str], float]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"accept": "application/json", "x-request-id": "ci-serving-smoke"}
    if body is not None:
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        elapsed_ms = (time.perf_counter() - started) * 1000
        response_body = json.loads(response.read().decode("utf-8"))
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        return response.status, response_body, response_headers, elapsed_ms


def request_text(url: str, timeout: float = 5.0) -> tuple[int, str, float]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=timeout) as response:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return response.status, response.read().decode("utf-8"), elapsed_ms


def wait_until_ready(base_url: str, attempts: int, delay_seconds: float) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        try:
            status, body, _, latency_ms = request_json(f"{base_url}/ready")
            if status == 200 and body.get("status") == "ready":
                return {
                    "attempt": attempt,
                    "latency_ms": round(latency_ms, 3),
                    "response": body,
                }
            last_error = f"unexpected readiness response: status={status}, body={body}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(delay_seconds)
    raise RuntimeError(f"service did not become ready after {attempts} attempts: {last_error}")


def run_smoke_test(base_url: str, attempts: int, delay_seconds: float) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    evidence: dict[str, Any] = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "checks": {},
    }

    evidence["checks"]["readiness"] = wait_until_ready(base_url, attempts, delay_seconds)

    health_status, health, _, health_latency = request_json(f"{base_url}/health")
    assert health_status == 200, health
    assert health.get("status") == "ok", health
    assert health.get("service") == "member-risk-api", health
    evidence["checks"]["health"] = {
        "status": health_status,
        "latency_ms": round(health_latency, 3),
        "response": health,
    }

    version_status, version, _, version_latency = request_json(f"{base_url}/version")
    assert version_status == 200, version
    assert version.get("service_version"), version
    assert version.get("build_sha"), version
    evidence["checks"]["version"] = {
        "status": version_status,
        "latency_ms": round(version_latency, 3),
        "response": version,
    }

    info_status, model_info, _, info_latency = request_json(f"{base_url}/model-info")
    assert info_status == 200, model_info
    assert model_info.get("model_alias") == "Champion", model_info
    assert "avg_booking_lead_days_12m" in model_info.get("numeric_features", []), model_info
    evidence["checks"]["model_info"] = {
        "status": info_status,
        "latency_ms": round(info_latency, 3),
        "response": model_info,
    }

    score_status, score, score_headers, score_latency = request_json(
        f"{base_url}/score/member-churn", method="POST", payload=SCORE_PAYLOAD
    )
    assert score_status == 200, score
    assert 0 <= float(score["churn_probability"]) <= 1, score
    assert score["risk_band"] in {"LOW", "MEDIUM", "HIGH"}, score
    assert score_headers.get("x-request-id") == score["request_id"], (score_headers, score)
    evidence["checks"]["score"] = {
        "status": score_status,
        "latency_ms": round(score_latency, 3),
        "response": score,
        "request_id_header": score_headers.get("x-request-id"),
    }

    metrics_status, metrics, metrics_latency = request_text(f"{base_url}/metrics")
    assert metrics_status == 200, metrics
    for metric_name in (
        "model_api_requests_total",
        "model_api_errors_total",
        "model_api_average_latency_ms",
    ):
        assert metric_name in metrics, metrics
    evidence["checks"]["metrics"] = {
        "status": metrics_status,
        "latency_ms": round(metrics_latency, 3),
        "required_metrics_present": True,
    }

    evidence["status"] = "PASS"
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the production-style scoring service.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--attempts", type=int, default=30)
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    evidence = run_smoke_test(args.base_url, args.attempts, args.delay_seconds)
    rendered = json.dumps(evidence, indent=2, sort_keys=True)
    print(rendered)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(rendered + "\n")


if __name__ == "__main__":
    main()
