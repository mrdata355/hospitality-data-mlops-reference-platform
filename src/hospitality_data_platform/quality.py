from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass
class QualityResult:
    table_name: str
    check_name: str
    status: str
    observed_value: float
    threshold_value: float
    details: str


def required_columns(df: pd.DataFrame, table_name: str, columns: list[str]) -> QualityResult:
    missing = sorted(set(columns) - set(df.columns))
    return QualityResult(table_name, "required_columns", "PASS" if not missing else "FAIL", float(len(missing)), 0.0, f"missing={missing}")


def unique_key(df: pd.DataFrame, table_name: str, columns: list[str]) -> QualityResult:
    duplicates = int(df.duplicated(columns).sum())
    return QualityResult(table_name, "unique_key", "PASS" if duplicates == 0 else "FAIL", float(duplicates), 0.0, f"key={columns}")


def null_rate(df: pd.DataFrame, table_name: str, column: str, max_rate: float) -> QualityResult:
    rate = float(df[column].isna().mean())
    return QualityResult(table_name, f"null_rate_{column}", "PASS" if rate <= max_rate else "FAIL", rate, max_rate, column)


def fail_on_errors(results: list[QualityResult]) -> None:
    failed = [r for r in results if r.status == "FAIL"]
    if failed:
        raise ValueError("Data quality failed: " + "; ".join(f"{r.table_name}.{r.check_name}: {r.details}" for r in failed))


def as_frame(results: list[QualityResult]) -> pd.DataFrame:
    return pd.DataFrame([asdict(r) for r in results])
