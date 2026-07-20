from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .config import GOLD, SILVER


def _read(name: str, dates: list[str]) -> pd.DataFrame:
    df = pd.read_csv(SILVER / f"{name}.csv")
    for column in dates:
        df[column] = pd.to_datetime(df[column])
    return df


def build_member_month_features() -> pd.DataFrame:
    members = _read("members", ["member_since_date"])
    points = _read("points_transactions", ["transaction_date"])
    stays = _read("resort_stays", ["booking_date", "check_in_date"])
    cases = _read("service_cases", ["case_created_at"])

    as_of_month = pd.Timestamp("2026-07-01")
    base = members[["member_id", "member_tier", "home_market", "member_since_date", "engagement_seed"]].copy()
    base["as_of_month"] = as_of_month
    base["tenure_months"] = ((as_of_month.year - base.member_since_date.dt.year) * 12 + (as_of_month.month - base.member_since_date.dt.month)).clip(lower=0)

    p = points[(points.transaction_date >= as_of_month - pd.DateOffset(months=12)) & (points.transaction_date < as_of_month)].copy()
    p["points_earned_12m"] = np.where(p.transaction_type == "EARN", p.points_amount, 0)
    p["points_redeemed_12m"] = np.where(p.transaction_type == "REDEEM", p.points_amount.abs(), 0)
    p["points_expired_12m"] = np.where(p.transaction_type == "EXPIRE", p.points_amount.abs(), 0)
    p_agg = p.groupby("member_id", as_index=False)[["points_earned_12m", "points_redeemed_12m", "points_expired_12m"]].sum()

    s = stays[(stays.check_in_date >= as_of_month - pd.DateOffset(months=12)) & (stays.check_in_date < as_of_month) & stays.stay_status.isin(["COMPLETED", "IN_HOUSE", "BOOKED"])].copy()
    s_agg = s.groupby("member_id", as_index=False).agg(stays_12m=("stay_id", "nunique"), room_nights_12m=("room_nights", "sum"), last_booking_date=("booking_date", "max"), net_room_revenue_12m=("net_room_revenue", "sum"))

    c = cases[(cases.case_created_at >= as_of_month - pd.Timedelta(days=90)) & (cases.case_created_at < as_of_month)].copy()
    c["escalated"] = c.case_priority.eq("ESCALATED").astype(int)
    c_agg = c.groupby("member_id", as_index=False).agg(service_cases_90d=("case_id", "nunique"), escalated_cases_90d=("escalated", "sum"), avg_resolution_hours_90d=("resolution_hours", "mean"))

    feat = base.merge(p_agg, on="member_id", how="left").merge(s_agg, on="member_id", how="left").merge(c_agg, on="member_id", how="left")
    numeric = ["points_earned_12m", "points_redeemed_12m", "points_expired_12m", "stays_12m", "room_nights_12m", "net_room_revenue_12m", "service_cases_90d", "escalated_cases_90d", "avg_resolution_hours_90d"]
    feat[numeric] = feat[numeric].fillna(0)
    feat["days_since_last_booking"] = (as_of_month - feat.last_booking_date).dt.days.fillna(999).clip(lower=0)
    feat["points_utilization_rate"] = (feat.points_redeemed_12m / feat.points_earned_12m.replace(0, np.nan)).fillna(0).clip(0, 3)
    feat["expired_share"] = (feat.points_expired_12m / (feat.points_earned_12m.abs() + 1)).clip(0, 3)

    risk = 1.6 * (0.20 + 0.008 * feat.days_since_last_booking - 0.18 * feat.stays_12m - 0.60 * feat.points_utilization_rate + 0.30 * feat.escalated_cases_90d + 0.12 * feat.service_cases_90d - 0.80 * feat.engagement_seed + 0.40 * feat.expired_share)
    probability = 1 / (1 + np.exp(-risk))
    deterministic_uniform = feat.member_id.map(lambda value: int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16) / 16**8)
    feat["churn_label"] = (deterministic_uniform < probability.clip(0.03, 0.92)).astype(int)
    feat["feature_created_at"] = pd.Timestamp.utcnow().isoformat()
    feat.to_csv(GOLD / "member_month_features.csv", index=False)
    return feat


def build_waterfall_features() -> pd.DataFrame:
    stays = _read("resort_stays", ["check_in_date"])
    resorts = _read("resorts", [])
    marketing = _read("marketing_events", ["touch_time"])

    valid = stays[stays.stay_status.isin(["COMPLETED", "IN_HOUSE", "BOOKED"])].copy()
    valid["week_start"] = valid.check_in_date.dt.to_period("W-SUN").dt.start_time
    weekly = valid.groupby(["resort_id", "week_start"], as_index=False).agg(arrivals=("reservation_id", "nunique"), room_nights=("room_nights", "sum"), net_room_revenue=("net_room_revenue", "sum"))

    full_weeks = pd.date_range(weekly.week_start.min(), weekly.week_start.max(), freq="W-MON")
    scaffold = pd.MultiIndex.from_product([resorts.resort_id, full_weeks], names=["resort_id", "week_start"]).to_frame(index=False)
    weekly = scaffold.merge(weekly, on=["resort_id", "week_start"], how="left").fillna({"arrivals": 0, "room_nights": 0, "net_room_revenue": 0})
    weekly = weekly.merge(resorts[["resort_id", "market", "capacity_units"]], on="resort_id", how="left")

    marketing["week_start"] = marketing.touch_time.dt.to_period("W-SUN").dt.start_time
    intensity = marketing.groupby(["market", "week_start"], as_index=False).size().rename(columns={"size": "campaign_intensity"})
    weekly = weekly.merge(intensity, on=["market", "week_start"], how="left")
    weekly["campaign_intensity"] = weekly.campaign_intensity.fillna(0)

    weekly = weekly.sort_values(["resort_id", "week_start"]).reset_index(drop=True)
    for lag in [1, 4, 13, 52]:
        weekly[f"lag_{lag}w"] = weekly.groupby("resort_id").arrivals.shift(lag)
    weekly["rolling_mean_4w"] = weekly.groupby("resort_id").arrivals.transform(lambda series: series.shift(1).rolling(4).mean())
    weekly["rolling_mean_13w"] = weekly.groupby("resort_id").arrivals.transform(lambda series: series.shift(1).rolling(13).mean())
    weekly["week_of_year"] = weekly.week_start.dt.isocalendar().week.astype(int)
    weekly["season_sin"] = np.sin(2 * np.pi * weekly.week_of_year / 52.0)
    weekly["season_cos"] = np.cos(2 * np.pi * weekly.week_of_year / 52.0)
    weekly["resort_code"] = weekly.resort_id.str.extract(r"(\d+)")[0].astype(int)
    weekly["month"] = weekly.week_start.dt.month
    weekly["quarter"] = weekly.week_start.dt.quarter
    weekly["year"] = weekly.week_start.dt.year
    weekly["feature_created_at"] = pd.Timestamp.utcnow().isoformat()
    weekly = weekly.dropna(subset=["lag_52w", "rolling_mean_13w"]).reset_index(drop=True)
    weekly.to_csv(GOLD / "waterfall_resort_week_features.csv", index=False)
    return weekly
