from __future__ import annotations

import sqlite3

import pandas as pd

from .config import DB_PATH
from .pipeline_dimensional import build_dimensions_and_facts
from .pipeline_ingestion import build_bronze, build_silver
from .pipeline_marts import build_gold_marts


def publish_sqlite(tables: dict[str, pd.DataFrame]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as conn:
        for name, df in tables.items():
            temp = df.copy()
            for column in temp.columns:
                if pd.api.types.is_datetime64_any_dtype(temp[column]):
                    temp[column] = temp[column].astype(str)
            temp.to_sql(name, conn, if_exists="replace", index=False)


def run_pipeline() -> dict[str, pd.DataFrame]:
    bronze = build_bronze()
    silver, quality = build_silver(bronze)
    model = build_dimensions_and_facts(silver)
    marts = build_gold_marts(silver, model)
    all_tables = {
        **{f"silver_{key}": value for key, value in silver.items()},
        **model,
        **marts,
        "data_quality_results": quality,
    }
    publish_sqlite(all_tables)
    return all_tables
