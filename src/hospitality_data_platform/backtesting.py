from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from .models import FORECAST_FEATURES


@dataclass(frozen=True)
class RollingOriginFold:
    fold: int
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    train_weeks: int
    validation_weeks: int


def _wape(actual: np.ndarray, prediction: np.ndarray) -> float:
    denominator = max(float(np.abs(actual).sum()), 1.0)
    return float(np.abs(actual - prediction).sum() / denominator)


def build_rolling_origin_folds(
    weeks: Iterable[pd.Timestamp | str],
    *,
    min_train_weeks: int = 52,
    validation_weeks: int = 8,
    step_weeks: int = 8,
    max_folds: int = 4,
) -> list[RollingOriginFold]:
    if min_train_weeks < 1 or validation_weeks < 1 or step_weeks < 1 or max_folds < 1:
        raise ValueError("Backtest window parameters must all be positive integers.")

    unique_weeks = pd.DatetimeIndex(pd.to_datetime(list(weeks))).drop_duplicates().sort_values()
    required = min_train_weeks + validation_weeks
    if len(unique_weeks) < required:
        raise ValueError(
            f"At least {required} unique weeks are required; found {len(unique_weeks)}."
        )

    candidates: list[RollingOriginFold] = []
    validation_start_index = min_train_weeks
    fold_number = 1
    while validation_start_index + validation_weeks <= len(unique_weeks):
        train = unique_weeks[:validation_start_index]
        validation = unique_weeks[
            validation_start_index : validation_start_index + validation_weeks
        ]
        candidates.append(
            RollingOriginFold(
                fold=fold_number,
                train_start=str(train.min().date()),
                train_end=str(train.max().date()),
                validation_start=str(validation.min().date()),
                validation_end=str(validation.max().date()),
                train_weeks=len(train),
                validation_weeks=len(validation),
            )
        )
        validation_start_index += step_weeks
        fold_number += 1

    selected = candidates[-max_folds:]
    return [
        RollingOriginFold(**{**asdict(fold), "fold": index})
        for index, fold in enumerate(selected, start=1)
    ]


def run_waterfall_backtest(
    features: pd.DataFrame,
    *,
    min_train_weeks: int = 52,
    validation_weeks: int = 8,
    step_weeks: int = 8,
    max_folds: int = 4,
) -> tuple[dict[str, object], pd.DataFrame]:
    required_columns = {
        "week_start",
        "resort_id",
        "arrivals",
        "lag_52w",
        *FORECAST_FEATURES,
    }
    missing = sorted(required_columns - set(features.columns))
    if missing:
        raise ValueError(f"Backtest input is missing required columns: {missing}")

    frame = features.copy()
    frame["week_start"] = pd.to_datetime(frame["week_start"])
    frame = frame.sort_values(["week_start", "resort_id"]).reset_index(drop=True)
    folds = build_rolling_origin_folds(
        frame["week_start"],
        min_train_weeks=min_train_weeks,
        validation_weeks=validation_weeks,
        step_weeks=step_weeks,
        max_folds=max_folds,
    )

    fold_metrics: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []

    for fold in folds:
        validation_start = pd.Timestamp(fold.validation_start)
        validation_end = pd.Timestamp(fold.validation_end)
        train = frame[frame.week_start < validation_start]
        valid = frame[(frame.week_start >= validation_start) & (frame.week_start <= validation_end)]
        if train.empty or valid.empty:
            raise RuntimeError(f"Fold {fold.fold} produced an empty train or validation set.")
        if train.week_start.max() >= valid.week_start.min():
            raise RuntimeError(f"Fold {fold.fold} violates temporal separation.")

        model = RandomForestRegressor(
            n_estimators=180,
            max_depth=10,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=1,
        )
        model.fit(train[FORECAST_FEATURES], train["arrivals"])
        prediction = np.clip(model.predict(valid[FORECAST_FEATURES]), 0, None)
        actual = valid["arrivals"].to_numpy(dtype=float)
        baseline = valid["lag_52w"].to_numpy(dtype=float)

        scored = valid[["resort_id", "week_start", "arrivals"]].copy()
        scored = scored.rename(columns={"arrivals": "actual"})
        scored["prediction"] = prediction
        scored["seasonal_baseline"] = baseline
        scored["absolute_error"] = np.abs(actual - prediction)
        scored["fold"] = fold.fold
        prediction_frames.append(scored)

        model_wape = _wape(actual, prediction)
        baseline_wape = _wape(actual, baseline)
        fold_metrics.append(
            {
                **asdict(fold),
                "train_rows": int(len(train)),
                "validation_rows": int(len(valid)),
                "wape": model_wape,
                "baseline_wape": baseline_wape,
                "forecast_bias": float(np.mean(prediction - actual)),
                "beats_baseline": bool(model_wape <= baseline_wape),
            }
        )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    actual = predictions["actual"].to_numpy(dtype=float)
    prediction = predictions["prediction"].to_numpy(dtype=float)
    baseline = predictions["seasonal_baseline"].to_numpy(dtype=float)

    per_resort: list[dict[str, object]] = []
    for resort_id, group in predictions.groupby("resort_id"):
        resort_actual = group["actual"].to_numpy(dtype=float)
        resort_prediction = group["prediction"].to_numpy(dtype=float)
        resort_baseline = group["seasonal_baseline"].to_numpy(dtype=float)
        per_resort.append(
            {
                "resort_id": str(resort_id),
                "rows": int(len(group)),
                "wape": _wape(resort_actual, resort_prediction),
                "baseline_wape": _wape(resort_actual, resort_baseline),
                "forecast_bias": float(np.mean(resort_prediction - resort_actual)),
            }
        )

    summary: dict[str, object] = {
        "evaluation_method": "expanding-window rolling-origin backtest",
        "fold_count": len(fold_metrics),
        "aggregate_wape": _wape(actual, prediction),
        "aggregate_baseline_wape": _wape(actual, baseline),
        "aggregate_forecast_bias": float(np.mean(prediction - actual)),
        "baseline_win_rate": float(np.mean([metric["beats_baseline"] for metric in fold_metrics])),
        "validation_rows": int(len(predictions)),
        "folds": fold_metrics,
        "per_resort": per_resort,
    }
    return summary, predictions
