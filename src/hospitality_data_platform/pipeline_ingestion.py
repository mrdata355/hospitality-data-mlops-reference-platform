from __future__ import annotations

import hashlib

import pandas as pd

from .config import BRONZE, GOLD, RAW, SILVER
from .quality import QualityResult, as_frame, fail_on_errors, null_rate, required_columns, unique_key

SOURCE_TABLES = [
    "members", "resorts", "campaigns", "reservations", "resort_stays",
    "points_transactions", "vacation_packages", "tour_events", "sales_contracts",
    "marketing_events", "service_cases", "labor_shifts"
]

DATE_COLUMNS = {
    "members": ["member_since_date", "updated_at"],
    "resorts": ["updated_at"],
    "campaigns": ["start_date", "end_date", "updated_at"],
    "reservations": ["booking_date", "check_in_date", "check_out_date", "updated_at"],
    "resort_stays": ["booking_date", "check_in_date", "check_out_date", "updated_at"],
    "points_transactions": ["transaction_date", "updated_at"],
    "vacation_packages": ["package_sale_date", "updated_at"],
    "tour_events": ["tour_date", "updated_at"],
    "sales_contracts": ["contract_date", "updated_at"],
    "marketing_events": ["touch_time", "updated_at"],
    "service_cases": ["case_created_at", "updated_at"],
    "labor_shifts": ["work_date", "updated_at"],
}


def _record_hash(row: pd.Series) -> str:
    text = "|".join("" if pd.isna(value) else str(value) for value in row.values)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_bronze(batch_id: str = "prodref_batch_001") -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for name in SOURCE_TABLES:
        path = RAW / f"{name}.csv"
        frame = pd.read_csv(path)
        frame["_source_file"] = path.name
        frame["_batch_id"] = batch_id
        frame["_ingested_at"] = pd.Timestamp.utcnow().isoformat()
        base_columns = [column for column in frame.columns if not column.startswith("_")]
        frame["_record_hash"] = frame[base_columns].apply(_record_hash, axis=1)
        frame.to_csv(BRONZE / f"{name}_raw.csv", index=False)
        tables[name] = frame
    return tables


def _parse_dates(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    output = frame.copy()
    for column in columns:
        if column in output.columns:
            output[column] = pd.to_datetime(output[column], errors="coerce")
    return output


def _latest(frame: pd.DataFrame, key: list[str]) -> pd.DataFrame:
    sort_columns = key + (["updated_at"] if "updated_at" in frame.columns else [])
    return frame.sort_values(sort_columns).drop_duplicates(key, keep="last").reset_index(drop=True)


def build_silver(bronze: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    silver: dict[str, pd.DataFrame] = {}
    results: list[QualityResult] = []

    for name, frame in bronze.items():
        silver[name] = _parse_dates(frame, DATE_COLUMNS.get(name, []))

    keys = {
        "members": ["member_id"], "resorts": ["resort_id"], "campaigns": ["campaign_id"],
        "reservations": ["reservation_id"], "resort_stays": ["stay_id"],
        "points_transactions": ["transaction_id"], "vacation_packages": ["package_id"],
        "tour_events": ["tour_id"], "sales_contracts": ["contract_id"],
        "marketing_events": ["touch_id"], "service_cases": ["case_id"],
        "labor_shifts": ["shift_id"],
    }
    for table, key in keys.items():
        silver[table] = _latest(silver[table], key)

    silver["members"]["member_tier"] = silver["members"]["member_tier"].str.title()
    silver["reservations"]["reservation_status"] = silver["reservations"]["reservation_status"].str.upper()
    silver["tour_events"]["tour_status"] = silver["tour_events"]["tour_status"].str.upper()
    silver["sales_contracts"]["contract_status"] = silver["sales_contracts"]["contract_status"].str.upper()
    silver["service_cases"]["case_priority"] = silver["service_cases"]["case_priority"].str.upper()

    checks = {
        "members": (["member_id", "member_tier", "home_market"], ["member_id"]),
        "resorts": (["resort_id", "market", "capacity_units"], ["resort_id"]),
        "reservations": (["reservation_id", "member_id", "resort_id", "check_in_date"], ["reservation_id"]),
        "points_transactions": (["transaction_id", "member_id", "transaction_date", "points_amount"], ["transaction_id"]),
        "tour_events": (["tour_id", "package_id", "prospect_id", "tour_status"], ["tour_id"]),
        "sales_contracts": (["contract_id", "package_id", "contract_status"], ["contract_id"]),
        "labor_shifts": (["shift_id", "resort_id", "work_date", "labor_hours"], ["shift_id"]),
    }
    for table, (columns, key) in checks.items():
        results.append(required_columns(silver[table], table, columns))
        results.append(unique_key(silver[table], table, key))
        results.append(null_rate(silver[table], table, key[0], 0.0))

    member_set = set(silver["members"].member_id)
    resort_set = set(silver["resorts"].resort_id)
    bad_member = int((~silver["reservations"].member_id.isin(member_set)).sum())
    bad_resort = int((~silver["reservations"].resort_id.isin(resort_set)).sum())
    results.append(QualityResult("reservations", "valid_member_fk", "PASS" if bad_member == 0 else "FAIL", float(bad_member), 0.0, "member_id"))
    results.append(QualityResult("reservations", "valid_resort_fk", "PASS" if bad_resort == 0 else "FAIL", float(bad_resort), 0.0, "resort_id"))

    fail_on_errors(results)
    for name, frame in silver.items():
        frame.to_csv(SILVER / f"{name}.csv", index=False)
    quality_frame = as_frame(results)
    quality_frame.to_csv(GOLD / "data_quality_results.csv", index=False)
    return silver, quality_frame
