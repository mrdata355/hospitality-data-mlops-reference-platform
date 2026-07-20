from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    catalog: str
    as_of_month: str
    model_alias: str
    max_wape: float
    require_baseline_improvement: bool


def parse_runtime_args(
    *,
    include_as_of_month: bool = False,
    include_model_alias: bool = False,
    include_acceptance: bool = False,
) -> RuntimeConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        default=os.getenv("PLATFORM_CATALOG", "hospitality_data_platform_dev"),
        help="Unity Catalog catalog for the active deployment target.",
    )
    if include_as_of_month:
        parser.add_argument(
            "--as-of-month",
            default=os.getenv("AS_OF_MONTH", "2026-07-01"),
            help="Feature cutoff month in YYYY-MM-DD format.",
        )
    if include_model_alias:
        parser.add_argument(
            "--model-alias",
            default=os.getenv("MODEL_ALIAS", "Champion"),
            help="Registered model alias used for production scoring.",
        )
    if include_acceptance:
        parser.add_argument(
            "--max-wape",
            type=float,
            default=float(os.getenv("MAX_FORECAST_WAPE", "0.30")),
            help="Maximum accepted validation WAPE.",
        )
        parser.add_argument(
            "--require-baseline-improvement",
            default=os.getenv("REQUIRE_BASELINE_IMPROVEMENT", "true"),
            choices=["true", "false"],
            help="Require the candidate to outperform the seasonal baseline.",
        )
    args = parser.parse_args()
    return RuntimeConfig(
        catalog=args.catalog,
        as_of_month=getattr(args, "as_of_month", "2026-07-01"),
        model_alias=getattr(args, "model_alias", "Champion"),
        max_wape=getattr(args, "max_wape", 0.30),
        require_baseline_improvement=(
            getattr(args, "require_baseline_improvement", "true") == "true"
        ),
    )


def table(catalog: str, schema: str, name: str) -> str:
    return f"{catalog}.{schema}.{name}"
