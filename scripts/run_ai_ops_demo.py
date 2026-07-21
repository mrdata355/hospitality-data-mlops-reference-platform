from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hospitality_data_platform.ai_ops import (  # noqa: E402
    IncidentSignal,
    IncidentType,
    build_default_orchestrator,
    run_evaluation_suite,
    to_primitive,
)


def main() -> None:
    output_dir = ROOT / "artifacts" / "ai_ops"
    output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = build_default_orchestrator(primary_failures=1)
    report = orchestrator.analyze(
        IncidentSignal(
            incident_id="INC-DEMO-2026-001",
            incident_type=IncidentType.FORECAST_DEGRADATION,
            metrics={
                "wape": 0.34,
                "baseline_wape": 0.26,
                "reservation_freshness_minutes": 47.0,
                "duplicate_rate": 0.001,
            },
            metadata={
                "affected_resorts": ["MCO-01", "LAS-02", "MYR-03"],
                "failed_checks": ["reservation_freshness"],
            },
        )
    )
    evaluation = run_evaluation_suite()

    report_path = output_dir / "demo_incident_report.json"
    evaluation_path = output_dir / "evaluation_summary.json"
    report_path.write_text(json.dumps(to_primitive(report), indent=2, sort_keys=True))
    evaluation_path.write_text(json.dumps(to_primitive(evaluation), indent=2, sort_keys=True))

    print(json.dumps({"report": str(report_path), "evaluation": str(evaluation_path)}, indent=2))


if __name__ == "__main__":
    main()
