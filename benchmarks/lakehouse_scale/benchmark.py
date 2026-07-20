#!/usr/bin/env python3
"""Deterministic Spark benchmark generator for hospitality-scale workloads.

The module has a credential-free planning mode that runs in CI and a Spark
generation mode intended for Databricks or another managed Spark runtime.
It never reads, prints, or stores cloud credentials.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

LARGE_RUN_CONFIRMATION = "YES_I_UNDERSTAND_COSTS"
REMOTE_PREFIXES = ("abfss://", "s3://", "gs://", "dbfs:/", "/Volumes/")
PROFILE_PATH = Path(__file__).with_name("configs") / "profiles.yml"
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class DomainPlan:
    domain: str
    target_logical_bytes: int
    estimated_rows: int
    output_partitions: int
    estimated_row_bytes: int
    weight: float


@dataclass(frozen=True)
class BenchmarkPlan:
    profile: str
    target_logical_bytes: int
    target_file_size_bytes: int
    total_output_partitions: int
    output_format: str
    domains: tuple[DomainPlan, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_commit() -> str:
    """Return the current source SHA without failing outside a Git checkout."""
    value = os.getenv("GITHUB_SHA") or os.getenv("SOURCE_COMMIT")
    if value:
        return value
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def load_config(path: Path = PROFILE_PATH) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("version") != 1:
        raise ValueError("Unsupported benchmark config version")
    domains = config.get("domains", {})
    if not domains:
        raise ValueError("At least one benchmark domain is required")
    weight_sum = sum(float(spec["weight"]) for spec in domains.values())
    if not math.isclose(weight_sum, 1.0, abs_tol=1e-9):
        raise ValueError(f"Domain weights must total 1.0; received {weight_sum}")
    return config


def build_plan(profile: str, config: dict[str, Any]) -> BenchmarkPlan:
    profiles = config["profiles"]
    if profile not in profiles:
        raise ValueError(f"Unknown profile {profile!r}; choose from {sorted(profiles)}")

    defaults = config["defaults"]
    target_bytes = int(profiles[profile]["target_logical_bytes"])
    target_file_size_bytes = int(defaults["target_file_size_mib"]) * 1024 * 1024
    total_partitions = max(1, math.ceil(target_bytes / target_file_size_bytes))

    domain_plans: list[DomainPlan] = []
    domain_items = list(config["domains"].items())
    assigned_bytes = 0
    assigned_partitions = 0
    for index, (name, spec) in enumerate(domain_items):
        weight = float(spec["weight"])
        row_bytes = int(spec["estimated_row_bytes"])
        is_last = index == len(domain_items) - 1
        domain_bytes = (
            target_bytes - assigned_bytes
            if is_last
            else max(1, round(target_bytes * weight))
        )
        partitions = (
            total_partitions - assigned_partitions
            if is_last
            else max(1, round(total_partitions * weight))
        )
        rows = max(1, math.ceil(domain_bytes / row_bytes))
        assigned_bytes += domain_bytes
        assigned_partitions += partitions
        domain_plans.append(
            DomainPlan(
                domain=name,
                target_logical_bytes=domain_bytes,
                estimated_rows=rows,
                output_partitions=partitions,
                estimated_row_bytes=row_bytes,
                weight=weight,
            )
        )

    return BenchmarkPlan(
        profile=profile,
        target_logical_bytes=target_bytes,
        target_file_size_bytes=target_file_size_bytes,
        total_output_partitions=total_partitions,
        output_format=str(defaults["output_format"]),
        domains=tuple(domain_plans),
    )


def validate_destination(
    profile: str,
    output_root: str,
    confirmation: str | None,
    config: dict[str, Any],
) -> None:
    if not output_root:
        raise ValueError("--output-root is required")

    require_confirmation = bool(
        config["profiles"][profile]["require_large_run_confirmation"]
    )
    if not require_confirmation:
        return
    if confirmation != LARGE_RUN_CONFIRMATION:
        raise ValueError(
            f"{profile} requires --confirm-large-run {LARGE_RUN_CONFIRMATION}"
        )
    if not output_root.startswith(REMOTE_PREFIXES):
        raise ValueError(
            f"{profile} must write to approved remote object storage or a Unity "
            "Catalog Volume, never to the repository or a developer laptop"
        )


def plan_as_dict(plan: BenchmarkPlan) -> dict[str, Any]:
    result = asdict(plan)
    result["domains"] = [asdict(domain) for domain in plan.domains]
    result["estimated_total_rows"] = sum(
        domain.estimated_rows for domain in plan.domains
    )
    return result


def _bp_hit(row_id: Any, basis_points: int, functions: Any) -> Any:
    return functions.pmod(row_id, functions.lit(10_000)) < functions.lit(basis_points)


def _base_frame(spark: Any, rows: int, partitions: int, history_days: int) -> Any:
    from pyspark.sql import functions as F

    return (
        spark.range(0, rows, numPartitions=partitions)
        .withColumnRenamed("id", "_row_id")
        .withColumn(
            "event_date",
            F.date_sub(F.current_date(), F.pmod(F.col("_row_id"), F.lit(history_days))),
        )
        .withColumn("event_month", F.date_format("event_date", "yyyy-MM"))
        .withColumn(
            "ingested_at",
            F.to_timestamp(
                F.from_unixtime(
                    F.unix_timestamp(F.current_timestamp())
                    - F.pmod(F.col("_row_id"), F.lit(3600))
                )
            ),
        )
    )


def _common_keys(df: Any, anomalies: dict[str, int]) -> Any:
    from pyspark.sql import functions as F

    hot = int(anomalies["hot_resort_records"])
    return (
        df.withColumn(
            "member_id",
            F.concat(
                F.lit("M"),
                F.lpad(
                    (F.pmod(F.col("_row_id"), F.lit(25_000_000)) + 1).cast("string"),
                    12,
                    "0",
                ),
            ),
        )
        .withColumn(
            "resort_id",
            F.when(_bp_hit(F.col("_row_id"), hot, F), F.lit(1)).otherwise(
                F.pmod(F.col("_row_id"), F.lit(250)) + 1
            ),
        )
        .withColumn(
            "source_record_hash",
            F.sha2(
                F.concat_ws(
                    "||",
                    F.col("_row_id").cast("string"),
                    F.col("event_date").cast("string"),
                ),
                256,
            ),
        )
    )


def _domain_frame(
    spark: Any,
    domain: str,
    rows: int,
    partitions: int,
    history_days: int,
    anomalies: dict[str, int],
) -> Any:
    """Build realistic mock records with Spark expressions only, never Python UDFs."""
    from pyspark.sql import functions as F

    df = _common_keys(_base_frame(spark, rows, partitions, history_days), anomalies)
    rid = F.col("_row_id")

    if domain == "members":
        df = (
            df.withColumn("member_id", F.concat(F.lit("M"), F.lpad((rid + 1).cast("string"), 12, "0")))
            .withColumn("join_date", F.date_sub(F.col("event_date"), F.pmod(rid, F.lit(3650))))
            .withColumn("tier", F.element_at(F.array(*[F.lit(x) for x in ("CLUB", "SELECT", "ELITE")]), F.pmod(rid, F.lit(3)) + 1))
            .withColumn("home_market", F.concat(F.lit("MKT-"), F.lpad((F.pmod(rid, F.lit(40)) + 1).cast("string"), 2, "0")))
            .withColumn("member_status", F.when(F.pmod(rid, F.lit(19)) == 0, "INACTIVE").otherwise("ACTIVE"))
            .withColumn("marketing_opt_in", F.pmod(rid, F.lit(5)) != 0)
        )
    elif domain == "reservations":
        df = (
            df.withColumn("reservation_id", F.concat(F.lit("R"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("booking_date", F.date_sub("event_date", F.pmod(rid, F.lit(180))))
            .withColumn("check_in_date", F.date_add("event_date", F.pmod(rid, F.lit(90))))
            .withColumn("nights", F.pmod(rid, F.lit(7)) + 1)
            .withColumn("party_size", F.pmod(rid, F.lit(6)) + 1)
            .withColumn("reservation_status", F.when(F.pmod(rid, F.lit(13)) == 0, "CANCELLED").otherwise("CONFIRMED"))
            .withColumn("revenue_amount", F.round(F.lit(119.0) + F.pmod(rid * 17, F.lit(1800)) / 10.0, 2))
            .withColumn("points_used", F.pmod(rid * 37, F.lit(90_000)))
        )
    elif domain == "stays":
        df = (
            df.withColumn("stay_id", F.concat(F.lit("S"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("reservation_id", F.concat(F.lit("R"), F.lpad((F.pmod(rid, F.lit(max(rows, 1))) + 1).cast("string"), 15, "0")))
            .withColumn("occupied_units", F.pmod(rid, F.lit(3)) + 1)
            .withColumn("room_nights", F.pmod(rid, F.lit(10)) + 1)
            .withColumn("stay_revenue", F.round(F.lit(149.0) + F.pmod(rid * 23, F.lit(3000)) / 10.0, 2))
            .withColumn("satisfaction_score", F.pmod(rid, F.lit(5)) + 1)
        )
    elif domain == "points_transactions":
        df = (
            df.withColumn("transaction_id", F.concat(F.lit("PT"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("transaction_type", F.element_at(F.array(*[F.lit(x) for x in ("EARN", "REDEEM", "EXPIRE", "ADJUST")]), F.pmod(rid, F.lit(4)) + 1))
            .withColumn("points_amount", (F.pmod(rid * 101, F.lit(50_000)) + 100).cast("long"))
            .withColumn("source_system", F.concat(F.lit("SRC-"), (F.pmod(rid, F.lit(8)) + 1).cast("string")))
        )
    elif domain == "tour_events":
        df = (
            df.withColumn("tour_event_id", F.concat(F.lit("T"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("package_id", F.concat(F.lit("PKG-"), F.lpad((F.pmod(rid, F.lit(2500)) + 1).cast("string"), 4, "0")))
            .withColumn("tour_status", F.element_at(F.array(*[F.lit(x) for x in ("BOOKED", "ARRIVED", "COMPLETED", "NO_SHOW")]), F.pmod(rid, F.lit(4)) + 1))
            .withColumn("sales_rep_key", F.pmod(rid, F.lit(12_000)) + 1)
            .withColumn("tour_minutes", F.pmod(rid * 7, F.lit(180)) + 30)
        )
    elif domain == "contracts":
        df = (
            df.withColumn("contract_id", F.concat(F.lit("C"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("tour_event_id", F.concat(F.lit("T"), F.lpad((F.pmod(rid, F.lit(max(rows, 1))) + 1).cast("string"), 15, "0")))
            .withColumn("contract_status", F.when(F.pmod(rid, F.lit(17)) == 0, "RESCINDED").otherwise("ACTIVE"))
            .withColumn("contract_value", F.round(F.lit(5000.0) + F.pmod(rid * 109, F.lit(450_000)) / 10.0, 2))
            .withColumn("term_months", (F.pmod(rid, F.lit(120)) + 12).cast("int"))
        )
    elif domain == "marketing_touches":
        null_bp = int(anomalies["null_business_fields"])
        df = (
            df.withColumn("touch_id", F.concat(F.lit("MT"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("campaign_id", F.concat(F.lit("CMP-"), F.lpad((F.pmod(rid, F.lit(5000)) + 1).cast("string"), 5, "0")))
            .withColumn(
                "channel",
                F.when(_bp_hit(rid, null_bp, F), F.lit(None).cast("string")).otherwise(
                    F.element_at(F.array(*[F.lit(x) for x in ("EMAIL", "SMS", "PAID_SEARCH", "SOCIAL", "CALL")]), F.pmod(rid, F.lit(5)) + 1)
                ),
            )
            .withColumn("impression_cost", F.round(F.pmod(rid * 13, F.lit(5000)) / 100.0, 2))
            .withColumn("converted", F.pmod(rid, F.lit(31)) == 0)
        )
    elif domain == "service_cases":
        df = (
            df.withColumn("case_id", F.concat(F.lit("SC"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("case_type", F.element_at(F.array(*[F.lit(x) for x in ("BILLING", "RESERVATION", "POINTS", "RESORT", "CONTRACT")]), F.pmod(rid, F.lit(5)) + 1))
            .withColumn("priority", F.element_at(F.array(*[F.lit(x) for x in ("LOW", "MEDIUM", "HIGH", "URGENT")]), F.pmod(rid, F.lit(4)) + 1))
            .withColumn("resolution_minutes", F.pmod(rid * 29, F.lit(20_000)) + 5)
            .withColumn("escalated", F.pmod(rid, F.lit(23)) == 0)
        )
    elif domain == "labor_shifts":
        df = (
            df.withColumn("shift_id", F.concat(F.lit("LS"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("employee_key", F.pmod(rid, F.lit(50_000)) + 1)
            .withColumn("department", F.element_at(F.array(*[F.lit(x) for x in ("FRONT_DESK", "HOUSEKEEPING", "SALES", "MAINTENANCE", "FOOD")]), F.pmod(rid, F.lit(5)) + 1))
            .withColumn("hours_worked", F.round(F.lit(4.0) + F.pmod(rid, F.lit(50)) / 10.0, 2))
            .withColumn("payroll_cost", F.round(F.lit(80.0) + F.pmod(rid * 19, F.lit(2400)) / 10.0, 2))
        )
    elif domain == "inventory_snapshots":
        df = (
            df.withColumn("snapshot_id", F.concat(F.lit("IS"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("room_type", F.concat(F.lit("ROOM-"), (F.pmod(rid, F.lit(12)) + 1).cast("string")))
            .withColumn("available_units", F.pmod(rid * 7, F.lit(500)))
            .withColumn("occupied_units", F.pmod(rid * 11, F.lit(450)))
            .withColumn("out_of_service_units", F.pmod(rid, F.lit(12)))
        )
    elif domain == "payments":
        df = (
            df.withColumn("payment_id", F.concat(F.lit("PAY"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("contract_id", F.concat(F.lit("C"), F.lpad((F.pmod(rid, F.lit(max(rows, 1))) + 1).cast("string"), 15, "0")))
            .withColumn("payment_method", F.element_at(F.array(*[F.lit(x) for x in ("CARD", "ACH", "CHECK")]), F.pmod(rid, F.lit(3)) + 1))
            .withColumn("payment_status", F.when(F.pmod(rid, F.lit(29)) == 0, "FAILED").otherwise("SETTLED"))
            .withColumn("payment_amount", F.round(F.lit(50.0) + F.pmod(rid * 43, F.lit(100_000)) / 100.0, 2))
        )
    elif domain == "web_events":
        df = (
            df.withColumn("web_event_id", F.concat(F.lit("WE"), F.lpad((rid + 1).cast("string"), 15, "0")))
            .withColumn("anonymous_session_id", F.concat(F.lit("SESSION-"), F.lpad((F.pmod(rid, F.lit(100_000_000)) + 1).cast("string"), 12, "0")))
            .withColumn("event_name", F.element_at(F.array(*[F.lit(x) for x in ("PAGE_VIEW", "SEARCH", "PACKAGE_VIEW", "FORM_START", "FORM_SUBMIT")]), F.pmod(rid, F.lit(5)) + 1))
            .withColumn("page_path", F.concat(F.lit("/resorts/"), (F.pmod(rid, F.lit(250)) + 1).cast("string")))
            .withColumn("device_type", F.element_at(F.array(*[F.lit(x) for x in ("MOBILE", "DESKTOP", "TABLET")]), F.pmod(rid, F.lit(3)) + 1))
        )
    else:
        raise ValueError(f"No generator registered for domain {domain!r}")

    late_bp = int(anomalies["late_arrivals"])
    df = df.withColumn(
        "ingested_at",
        F.when(
            _bp_hit(rid, late_bp, F),
            F.current_timestamp() + F.expr("INTERVAL 3 DAY"),
        ).otherwise(F.col("ingested_at")),
    )

    duplicate_bp = int(anomalies["duplicate_rows"])
    duplicates = df.filter(_bp_hit(rid, duplicate_bp, F))
    return df.unionByName(duplicates).drop("_row_id")


def _storage_summary(spark: Any, path: str) -> tuple[int, int]:
    hadoop = spark._jsc.hadoopConfiguration()
    jpath = spark._jvm.org.apache.hadoop.fs.Path(path)
    filesystem = jpath.getFileSystem(hadoop)
    summary = filesystem.getContentSummary(jpath)
    return int(summary.getLength()), int(summary.getFileCount())


def _write_json(spark: Any, path: str, payload: dict[str, Any]) -> None:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    hadoop = spark._jsc.hadoopConfiguration()
    jpath = spark._jvm.org.apache.hadoop.fs.Path(path)
    filesystem = jpath.getFileSystem(hadoop)
    parent = jpath.getParent()
    if parent is not None:
        filesystem.mkdirs(parent)
    stream = filesystem.create(jpath, True)
    try:
        stream.write(bytearray(data))
    finally:
        stream.close()


def execute_plan(
    plan: BenchmarkPlan,
    output_root: str,
    run_id: str,
    config: dict[str, Any],
    full_reconciliation: bool,
) -> dict[str, Any]:
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError(
            "Generation mode requires PySpark or a Databricks runtime. "
            "Use --mode plan for credential-free validation."
        ) from exc

    spark = SparkSession.builder.appName(
        f"hospitality-scale-benchmark-{plan.profile}"
    ).getOrCreate()
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    spark.conf.set(
        "spark.sql.adaptive.advisoryPartitionSizeInBytes",
        str(plan.target_file_size_bytes),
    )

    started = utc_now()
    started_clock = time.perf_counter()
    domain_results: list[dict[str, Any]] = []
    defaults = config["defaults"]
    anomalies = defaults["anomaly_basis_points"]
    history_days = int(defaults["history_days"])
    run_root = f"{output_root.rstrip('/')}/{plan.profile}/{run_id}"

    for domain in plan.domains:
        domain_started = time.perf_counter()
        frame = _domain_frame(
            spark=spark,
            domain=domain.domain,
            rows=domain.estimated_rows,
            partitions=domain.output_partitions,
            history_days=history_days,
            anomalies=anomalies,
        )
        domain_path = f"{run_root}/raw/{domain.domain}"
        (
            frame.repartition(domain.output_partitions)
            .write.mode("overwrite")
            .format(plan.output_format)
            .partitionBy("event_month")
            .save(domain_path)
        )

        actual_rows = None
        if full_reconciliation:
            actual_rows = spark.read.format(plan.output_format).load(domain_path).count()

        storage_bytes, file_count = _storage_summary(spark, domain_path)
        domain_results.append(
            {
                **asdict(domain),
                "actual_rows": actual_rows,
                "actual_storage_bytes": storage_bytes,
                "file_count": file_count,
                "runtime_seconds": round(time.perf_counter() - domain_started, 3),
                "path": domain_path,
                "status": "PASSED",
            }
        )

    manifest = {
        "benchmark_id": f"hospitality-{plan.profile}-{run_id}",
        "status": "PASSED",
        "profile": plan.profile,
        "source_commit": source_commit(),
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "runtime_seconds": round(time.perf_counter() - started_clock, 3),
        "target_logical_bytes": plan.target_logical_bytes,
        "actual_storage_bytes": sum(
            result["actual_storage_bytes"] for result in domain_results
        ),
        "expected_rows": sum(result["estimated_rows"] for result in domain_results),
        "actual_rows": (
            sum(result["actual_rows"] for result in domain_results)
            if full_reconciliation
            else None
        ),
        "full_reconciliation": full_reconciliation,
        "output_format": plan.output_format,
        "output_root": output_root,
        "credentials_committed": False,
        "anomaly_basis_points": anomalies,
        "domains": domain_results,
        "limitations": [
            "Generated records are synthetic and do not represent customer behavior.",
            "Target size is logical input volume; actual compressed storage is recorded separately.",
            "Performance depends on runtime, node type, worker count, autoscaling, and cloud region.",
        ],
    }
    _write_json(spark, f"{run_root}/evidence/run_manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="sample")
    parser.add_argument("--mode", choices=("plan", "generate"), default="plan")
    parser.add_argument("--output-root", default="./benchmark-output")
    parser.add_argument(
        "--run-id",
        default=os.getenv("BENCHMARK_RUN_ID")
        or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--confirm-large-run")
    parser.add_argument("--full-reconciliation", action="store_true")
    parser.add_argument("--config", type=Path, default=PROFILE_PATH)
    parser.add_argument("--manifest-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not SAFE_RUN_ID.fullmatch(args.run_id):
        raise ValueError("--run-id contains unsupported characters")

    config = load_config(args.config)
    validate_destination(
        args.profile, args.output_root, args.confirm_large_run, config
    )
    plan = build_plan(args.profile, config)

    if args.mode == "plan":
        result: dict[str, Any] = {
            "status": "PLANNED_NOT_EXECUTED",
            "generated_at_utc": utc_now(),
            "source_commit": source_commit(),
            "credentials_required": False,
            "plan": plan_as_dict(plan),
        }
    else:
        result = execute_plan(
            plan=plan,
            output_root=args.output_root,
            run_id=args.run_id,
            config=config,
            full_reconciliation=args.full_reconciliation,
        )

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.manifest_out:
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
