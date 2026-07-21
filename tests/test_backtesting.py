import pandas as pd

from hospitality_data_platform.backtesting import build_rolling_origin_folds


def test_rolling_origin_folds_are_temporally_separated_and_expanding():
    weeks = pd.date_range("2024-01-01", periods=92, freq="W-MON")
    folds = build_rolling_origin_folds(
        weeks,
        min_train_weeks=52,
        validation_weeks=8,
        step_weeks=8,
        max_folds=4,
    )

    assert len(folds) == 4
    previous_train_weeks = 0
    for fold in folds:
        assert pd.Timestamp(fold.train_end) < pd.Timestamp(fold.validation_start)
        assert fold.validation_weeks == 8
        assert fold.train_weeks > previous_train_weeks
        previous_train_weeks = fold.train_weeks


def test_rolling_origin_folds_reject_insufficient_history():
    weeks = pd.date_range("2026-01-05", periods=20, freq="W-MON")

    try:
        build_rolling_origin_folds(weeks, min_train_weeks=16, validation_weeks=8)
    except ValueError as exc:
        assert "At least 24 unique weeks" in str(exc)
    else:
        raise AssertionError("Expected insufficient history to raise ValueError.")
