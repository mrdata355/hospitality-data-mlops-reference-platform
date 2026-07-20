from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hospitality_data_platform.data_generation import generate_all
from hospitality_data_platform.features import build_member_month_features, build_waterfall_features
from hospitality_data_platform.models import train_churn_model, train_waterfall_model
from hospitality_data_platform.monitoring import run_monitoring
from hospitality_data_platform.pipeline import run_pipeline


def main() -> None:
    counts = generate_all()
    run_pipeline()
    member_features = build_member_month_features()
    forecast_features = build_waterfall_features()
    churn_metrics = train_churn_model(member_features)
    forecast_metrics = train_waterfall_model(forecast_features)
    monitoring = run_monitoring()

    summary = {
        "source_counts": counts,
        "member_feature_rows": len(member_features),
        "forecast_feature_rows": len(forecast_features),
        "churn_metrics": churn_metrics,
        "forecast_metrics": forecast_metrics,
        "monitoring": monitoring,
    }
    path = ROOT / "artifacts" / "run_summary.json"
    path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
