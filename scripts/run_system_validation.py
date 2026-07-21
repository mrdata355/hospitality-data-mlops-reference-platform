from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smoke_test_serving import run_smoke_test

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION = ROOT / "examples/sample_outputs/validation_summary.json"
DEFAULT_BACKTEST = ROOT / "artifacts/metrics/waterfall_backtest_metrics.json"
DEFAULT_EVIDENCE = ROOT / "artifacts/validation/system_validation.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required evidence file is unavailable: {path}")
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _validate_platform_evidence(validation: dict[str, Any]) -> None:
    acceptance = validation.get("acceptance", {})
    failed = sorted(name for name, passed in acceptance.items() if passed is not True)
    if failed:
        raise RuntimeError(f"Platform acceptance gates failed: {failed}")
    if validation.get("data_profile", {}).get("synthetic_data_only") is not True:
        raise RuntimeError("System validation must use generated non-production data only.")


def build_report(
    *,
    base_url: str,
    validation: dict[str, Any],
    backtest: dict[str, Any] | None,
    serving: dict[str, Any],
) -> dict[str, Any]:
    _validate_platform_evidence(validation)
    if serving.get("status") != "PASS":
        raise RuntimeError("Serving validation did not pass.")

    health = serving["checks"]["health"]["response"]
    version = serving["checks"]["version"]["response"]
    score = serving["checks"]["score"]["response"]
    profile = validation["data_profile"]
    row_counts = profile["source_row_counts"]
    member_risk = validation["member_risk"]
    forecast = validation["waterfall_forecast"]

    rolling_origin: dict[str, Any] | None = None
    if backtest is not None:
        rolling_origin = {
            "fold_count": int(backtest["fold_count"]),
            "validation_rows": int(backtest["validation_rows"]),
            "wape": float(backtest["aggregate_wape"]),
            "baseline_wape": float(backtest["aggregate_baseline_wape"]),
            "baseline_win_rate": float(backtest["baseline_win_rate"]),
        }

    return {
        "status": "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url.rstrip("/"),
        "data_boundary": {
            "synthetic_data_only": True,
            "source_domains": int(profile["source_domains"]),
            "reservation_rows": int(row_counts["reservations"]),
            "labor_shift_rows": int(row_counts["labor_shifts"]),
        },
        "model_evidence": {
            "member_risk_roc_auc": float(member_risk["roc_auc"]),
            "forecast_wape": float(forecast["wape"]),
            "seasonal_baseline_wape": float(forecast["baseline_wape"]),
            "rolling_origin": rolling_origin,
        },
        "serving_evidence": {
            "environment": health["environment"],
            "service_version": version["service_version"],
            "build_sha": version["build_sha"],
            "model_alias": score["model_alias"],
            "sample_churn_probability": float(score["churn_probability"]),
            "sample_risk_band": score["risk_band"],
            "request_id": score["request_id"],
            "health_latency_ms": float(serving["checks"]["health"]["latency_ms"]),
            "score_latency_ms": float(serving["checks"]["score"]["latency_ms"]),
            "required_metrics_present": bool(
                serving["checks"]["metrics"]["required_metrics_present"]
            ),
        },
        "claim_boundary": (
            "Generated-data system validation; not customer-impact evidence or proof of a live "
            "enterprise deployment."
        ),
    }


def render_console_summary(report: dict[str, Any]) -> str:
    data = report["data_boundary"]
    models = report["model_evidence"]
    serving = report["serving_evidence"]
    lines = [
        "SYSTEM VALIDATION: PASS",
        (
            f"Data: {data['source_domains']} domains | "
            f"{data['reservation_rows']:,} reservations | "
            f"{data['labor_shift_rows']:,} labor shifts"
        ),
        f"Member risk: ROC AUC {models['member_risk_roc_auc']:.4f}",
        (
            f"Forecast: WAPE {models['forecast_wape']:.4f} | "
            f"seasonal baseline {models['seasonal_baseline_wape']:.4f}"
        ),
    ]
    rolling = models.get("rolling_origin")
    if rolling:
        lines.append(
            f"Rolling origin: {rolling['fold_count']} folds | WAPE {rolling['wape']:.4f} | "
            f"baseline {rolling['baseline_wape']:.4f}"
        )
    lines.extend(
        [
            (
                f"Serving: {serving['environment']} | v{serving['service_version']} | "
                f"build {serving['build_sha']}"
            ),
            (
                f"Sample score: {serving['sample_risk_band']} risk | "
                f"probability {serving['sample_churn_probability']:.4f} | "
                f"{serving['score_latency_ms']:.2f} ms"
            ),
            f"Endpoint: {report['base_url']}",
            f"Boundary: {report['claim_boundary']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate data, model, temporal, serving, and metrics contracts."
    )
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--backtest", type=Path, default=DEFAULT_BACKTEST)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--attempts", type=int, default=30)
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--allow-missing-backtest", action="store_true")
    args = parser.parse_args()

    validation = _load_json(args.validation)
    backtest = None
    if args.backtest.exists():
        backtest = _load_json(args.backtest)
    elif not args.allow_missing_backtest:
        raise FileNotFoundError(
            f"Rolling-origin evidence is unavailable: {args.backtest}. Run `make backtest`."
        )

    serving = run_smoke_test(args.base_url, args.attempts, args.delay_seconds)
    report = build_report(
        base_url=args.base_url,
        validation=validation,
        backtest=backtest,
        serving=serving,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(rendered + "\n")
    print(render_console_summary(report))
    print(f"Evidence: {args.evidence}")


if __name__ == "__main__":
    main()
