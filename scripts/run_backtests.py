from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hospitality_data_platform.backtesting import run_waterfall_backtest
from hospitality_data_platform.config import GOLD, METRICS, PREDICTIONS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run expanding-window rolling-origin validation for the resort-week model."
    )
    parser.add_argument("--min-train-weeks", type=int, default=52)
    parser.add_argument("--validation-weeks", type=int, default=8)
    parser.add_argument("--step-weeks", type=int, default=8)
    parser.add_argument("--max-folds", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = GOLD / "waterfall_resort_week_features.csv"
    if not source.exists():
        raise FileNotFoundError(
            f"Feature file not found: {source}. Run python scripts/run_all.py first."
        )

    features = pd.read_csv(source, parse_dates=["week_start"])
    summary, predictions = run_waterfall_backtest(
        features,
        min_train_weeks=args.min_train_weeks,
        validation_weeks=args.validation_weeks,
        step_weeks=args.step_weeks,
        max_folds=args.max_folds,
    )

    METRICS.mkdir(parents=True, exist_ok=True)
    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    metrics_path = METRICS / "waterfall_backtest_metrics.json"
    predictions_path = PREDICTIONS / "waterfall_backtest_predictions.csv"
    metrics_path.write_text(json.dumps(summary, indent=2))
    predictions.to_csv(predictions_path, index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
