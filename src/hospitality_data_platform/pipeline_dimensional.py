from __future__ import annotations

import numpy as np
import pandas as pd

from .config import GOLD


def _date_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y%m%d").astype(int)


def build_dimensions_and_facts(s: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}

    dim_member = s["members"][["member_id", "member_tier", "home_market", "member_since_date", "active_flag"]].copy()
    dim_member.insert(0, "member_key", np.arange(1, len(dim_member) + 1))
    output["dim_member"] = dim_member

    dim_resort = s["resorts"][["resort_id", "resort_name", "market", "region", "capacity_units", "property_type", "active_flag"]].copy()
    dim_resort.insert(0, "resort_key", np.arange(1, len(dim_resort) + 1))
    output["dim_resort"] = dim_resort

    dim_campaign = s["campaigns"][["campaign_id", "campaign_name", "channel", "target_market", "start_date", "end_date", "budget"]].copy()
    dim_campaign.insert(0, "campaign_key", np.arange(1, len(dim_campaign) + 1))
    output["dim_campaign"] = dim_campaign

    minimum_date = min(pd.to_datetime(s["reservations"].booking_date).min(), pd.to_datetime(s["points_transactions"].transaction_date).min())
    maximum_date = max(pd.to_datetime(s["reservations"].check_out_date).max(), pd.to_datetime(s["labor_shifts"].work_date).max())
    dates = pd.date_range(minimum_date, maximum_date, freq="D")
    dim_date = pd.DataFrame({"full_date": dates})
    dim_date["date_key"] = dim_date.full_date.dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date.full_date.dt.year
    dim_date["quarter"] = dim_date.full_date.dt.quarter
    dim_date["month"] = dim_date.full_date.dt.month
    dim_date["month_name"] = dim_date.full_date.dt.month_name()
    dim_date["week_of_year"] = dim_date.full_date.dt.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dim_date.full_date.dt.day_name()
    dim_date["weekend_flag"] = dim_date.full_date.dt.dayofweek.isin([5, 6]).astype(int)
    output["dim_date"] = dim_date[["date_key", "full_date", "year", "quarter", "month", "month_name", "week_of_year", "day_of_week", "weekend_flag"]]

    member_map = dim_member.set_index("member_id").member_key
    resort_map = dim_resort.set_index("resort_id").resort_key
    campaign_map = dim_campaign.set_index("campaign_id").campaign_key

    fact_reservation = s["reservations"].copy()
    fact_reservation["member_key"] = fact_reservation.member_id.map(member_map)
    fact_reservation["resort_key"] = fact_reservation.resort_id.map(resort_map)
    fact_reservation["booking_date_key"] = _date_key(fact_reservation.booking_date)
    fact_reservation["check_in_date_key"] = _date_key(fact_reservation.check_in_date)
    output["fact_reservation"] = fact_reservation[["reservation_id", "member_key", "resort_key", "booking_date_key", "check_in_date_key", "reservation_status", "room_nights", "points_redeemed", "net_room_revenue"]]

    fact_stay = s["resort_stays"].copy()
    fact_stay["member_key"] = fact_stay.member_id.map(member_map)
    fact_stay["resort_key"] = fact_stay.resort_id.map(resort_map)
    fact_stay["check_in_date_key"] = _date_key(fact_stay.check_in_date)
    output["fact_stay"] = fact_stay[["stay_id", "reservation_id", "member_key", "resort_key", "check_in_date_key", "stay_status", "room_nights", "points_redeemed", "net_room_revenue"]]

    fact_points = s["points_transactions"].copy()
    fact_points["member_key"] = fact_points.member_id.map(member_map)
    fact_points["transaction_date_key"] = _date_key(fact_points.transaction_date)
    output["fact_points_transaction"] = fact_points[["transaction_id", "member_key", "transaction_date_key", "transaction_type", "points_amount"]]

    fact_tours = s["tour_events"].copy()
    fact_tours["tour_date_key"] = _date_key(fact_tours.tour_date)
    output["fact_tour_event"] = fact_tours[["tour_id", "package_id", "prospect_id", "tour_date_key", "tour_status", "market"]]

    fact_contracts = s["sales_contracts"].copy()
    fact_contracts["contract_date_key"] = _date_key(fact_contracts.contract_date)
    output["fact_sales_contract"] = fact_contracts[["contract_id", "package_id", "prospect_id", "contract_date_key", "contract_status", "net_contract_value"]]

    fact_cases = s["service_cases"].copy()
    fact_cases["member_key"] = fact_cases.member_id.map(member_map)
    fact_cases["case_date_key"] = _date_key(fact_cases.case_created_at)
    output["fact_service_case"] = fact_cases[["case_id", "member_key", "case_date_key", "case_priority", "resolution_hours", "case_status"]]

    fact_labor = s["labor_shifts"].copy()
    fact_labor["resort_key"] = fact_labor.resort_id.map(resort_map)
    fact_labor["work_date_key"] = _date_key(fact_labor.work_date)
    output["fact_labor_shift"] = fact_labor[["shift_id", "resort_key", "employee_id", "work_date_key", "labor_hours", "payroll_cost"]]

    fact_touch = s["marketing_events"].copy()
    fact_touch["campaign_key"] = fact_touch.campaign_id.map(campaign_map)
    fact_touch["touch_date_key"] = _date_key(fact_touch.touch_time)
    output["fact_marketing_touch"] = fact_touch[["touch_id", "prospect_id", "member_id", "campaign_key", "touch_date_key", "channel", "market"]]

    for name, frame in output.items():
        frame.to_csv(GOLD / f"{name}.csv", index=False)
    return output
