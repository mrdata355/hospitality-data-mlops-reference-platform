from __future__ import annotations

import numpy as np
import pandas as pd

from .config import GOLD


def build_gold_marts(s: dict[str, pd.DataFrame], model: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    del model
    marts: dict[str, pd.DataFrame] = {}

    stays = s["resort_stays"].copy()
    stays["month_start"] = stays.check_in_date.dt.to_period("M").dt.to_timestamp()
    valid_stays = stays[stays.stay_status.isin(["BOOKED", "COMPLETED", "IN_HOUSE"])].copy()
    resort_monthly = valid_stays.groupby(["resort_id", "month_start"], as_index=False).agg(
        reservation_count=("reservation_id", "nunique"), unique_members=("member_id", "nunique"),
        room_nights=("room_nights", "sum"), net_room_revenue=("net_room_revenue", "sum"),
        points_redeemed=("points_redeemed", "sum"),
    )
    resort_monthly = resort_monthly.merge(s["resorts"][["resort_id", "resort_name", "market", "capacity_units"]], on="resort_id", how="left")
    resort_monthly["adr"] = resort_monthly.net_room_revenue / resort_monthly.room_nights.replace(0, np.nan)
    resort_monthly["occupancy_proxy"] = resort_monthly.room_nights / (resort_monthly.capacity_units * resort_monthly.month_start.dt.days_in_month)
    marts["resort_monthly_performance"] = resort_monthly

    packages = s["vacation_packages"].copy()
    packages["month_start"] = packages.package_sale_date.dt.to_period("M").dt.to_timestamp()
    tours = s["tour_events"].groupby(["package_id", "prospect_id"], as_index=False).agg(
        tour_scheduled=("tour_id", "nunique"), showed_tour=("tour_status", lambda values: int((values == "SHOW").any())),
    )
    contracts = s["sales_contracts"].groupby(["package_id", "prospect_id"], as_index=False).agg(
        signed_contract=("contract_status", lambda values: int((values == "SIGNED").any())),
        net_contract_value=("net_contract_value", "sum"),
    )
    funnel = packages.merge(tours, on=["package_id", "prospect_id"], how="left").merge(contracts, on=["package_id", "prospect_id"], how="left")
    columns = ["tour_scheduled", "showed_tour", "signed_contract", "net_contract_value"]
    funnel[columns] = funnel[columns].fillna(0)
    attribution = funnel.groupby(["campaign_id", "lead_channel", "market", "month_start"], as_index=False).agg(
        packages_sold=("package_id", "nunique"), tours_scheduled=("tour_scheduled", "sum"),
        tours_showed=("showed_tour", "sum"), contracts_signed=("signed_contract", "sum"),
        net_contract_value=("net_contract_value", "sum"),
    )
    attribution = attribution.merge(s["campaigns"][["campaign_id", "budget"]], on="campaign_id", how="left")
    attribution["tour_show_rate"] = attribution.tours_showed / attribution.tours_scheduled.replace(0, np.nan)
    attribution["show_to_contract_rate"] = attribution.contracts_signed / attribution.tours_showed.replace(0, np.nan)
    attribution["roas"] = attribution.net_contract_value / attribution.budget.replace(0, np.nan)
    marts["campaign_tour_sales_attribution"] = attribution

    points = s["points_transactions"].copy()
    points["month_start"] = points.transaction_date.dt.to_period("M").dt.to_timestamp()
    points["points_earned"] = np.where(points.transaction_type == "EARN", points.points_amount, 0)
    points["points_redeemed"] = np.where(points.transaction_type == "REDEEM", points.points_amount.abs(), 0)
    points["points_expired"] = np.where(points.transaction_type == "EXPIRE", points.points_amount.abs(), 0)
    point_month = points.groupby(["member_id", "month_start"], as_index=False)[["points_earned", "points_redeemed", "points_expired"]].sum()
    stay_month = valid_stays.groupby(["member_id", "month_start"], as_index=False).agg(stay_count=("stay_id", "nunique"), room_nights=("room_nights", "sum"))
    cases = s["service_cases"].copy()
    cases["month_start"] = cases.case_created_at.dt.to_period("M").dt.to_timestamp()
    cases["escalated"] = cases.case_priority.eq("ESCALATED").astype(int)
    case_month = cases.groupby(["member_id", "month_start"], as_index=False).agg(service_cases=("case_id", "nunique"), escalated_cases=("escalated", "sum"))
    utilization = point_month.merge(stay_month, on=["member_id", "month_start"], how="outer").merge(case_month, on=["member_id", "month_start"], how="outer").fillna(0)
    utilization = utilization.merge(s["members"][["member_id", "member_tier", "home_market"]], on="member_id", how="left")
    utilization["points_utilization_rate"] = utilization.points_redeemed / utilization.points_earned.replace(0, np.nan)
    marts["member_points_utilization"] = utilization

    valid_stays["business_date"] = valid_stays.check_in_date.dt.date
    daily_stays = valid_stays.groupby(["resort_id", "business_date"], as_index=False).agg(
        arrivals=("reservation_id", "nunique"), occupied_unit_nights=("room_nights", "sum"), net_room_revenue=("net_room_revenue", "sum")
    )
    labor_source = s["labor_shifts"].copy()
    labor_source["business_date"] = labor_source.work_date.dt.date
    labor = labor_source.groupby(["resort_id", "business_date"], as_index=False).agg(labor_hours=("labor_hours", "sum"), payroll_cost=("payroll_cost", "sum"))
    efficiency = daily_stays.merge(labor, on=["resort_id", "business_date"], how="left").merge(s["resorts"][["resort_id", "resort_name", "market"]], on="resort_id", how="left")
    efficiency[["labor_hours", "payroll_cost"]] = efficiency[["labor_hours", "payroll_cost"]].fillna(0)
    efficiency["payroll_cost_per_occupied_unit_night"] = efficiency.payroll_cost / efficiency.occupied_unit_nights.replace(0, np.nan)
    efficiency["revenue_per_labor_hour"] = efficiency.net_room_revenue / efficiency.labor_hours.replace(0, np.nan)
    p95 = efficiency.groupby("resort_id").payroll_cost_per_occupied_unit_night.transform(lambda values: values.quantile(0.95))
    efficiency["staffing_anomaly_flag"] = (efficiency.payroll_cost_per_occupied_unit_night > p95).astype(int)
    marts["resort_labor_efficiency"] = efficiency

    marts["semantic_metric_layer"] = pd.DataFrame([
        ("net_room_revenue", "SUM(net_room_revenue)", "USD", "gold.resort_monthly_performance"),
        ("adr", "SUM(net_room_revenue) / NULLIF(SUM(room_nights),0)", "USD", "gold.resort_monthly_performance"),
        ("tour_show_rate", "SUM(tours_showed) / NULLIF(SUM(tours_scheduled),0)", "RATE", "gold.campaign_tour_sales_attribution"),
        ("show_to_contract_rate", "SUM(contracts_signed) / NULLIF(SUM(tours_showed),0)", "RATE", "gold.campaign_tour_sales_attribution"),
        ("revenue_per_labor_hour", "SUM(net_room_revenue) / NULLIF(SUM(labor_hours),0)", "USD", "gold.resort_labor_efficiency"),
    ], columns=["metric_name", "formula", "format", "source_table"])

    for name, frame in marts.items():
        frame.to_csv(GOLD / f"{name}.csv", index=False)
    return marts
