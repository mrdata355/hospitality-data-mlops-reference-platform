from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RAW, SEED


def _save(df: pd.DataFrame, name: str) -> None:
    df.to_csv(RAW / f"{name}.csv", index=False)


def _id(prefix: str, n: int, width: int = 6) -> list[str]:
    return [f"{prefix}{i:0{width}d}" for i in range(1, n + 1)]


def generate_all(seed: int = SEED) -> dict[str, int]:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2026-06-30")

    resorts = pd.DataFrame({
        "resort_id": _id("R", 8, 3),
        "resort_name": ["Seabreeze Orlando", "Harbor Point Miami", "Desert Vista Las Vegas", "Mountain Lodge Gatlinburg", "Ocean Walk Myrtle Beach", "Island Club Honolulu", "Bayfront San Diego", "City Suites New York"],
        "market": ["Orlando", "Miami", "Las Vegas", "Gatlinburg", "Myrtle Beach", "Honolulu", "San Diego", "New York"],
        "region": ["Southeast", "Southeast", "West", "Southeast", "Southeast", "Pacific", "West", "Northeast"],
        "capacity_units": [420, 260, 520, 210, 310, 280, 240, 190],
        "property_type": ["Resort", "Resort", "Resort", "Lodge", "Resort", "Resort", "Resort", "Urban"],
        "active_flag": 1,
        "updated_at": end,
    })
    _save(resorts, "resorts")

    n_members = 1200
    member_ids = _id("M", n_members)
    member_since = start - pd.to_timedelta(rng.integers(30, 2500, n_members), unit="D")
    member_tier = rng.choice(["Member", "Elite", "Premier", "Max"], n_members, p=[0.52, 0.25, 0.15, 0.08])
    home_market = rng.choice(resorts["market"], n_members)
    engagement = rng.beta(2.2, 2.0, n_members)
    members = pd.DataFrame({
        "member_id": member_ids,
        "first_name": [f"Member{i}" for i in range(1, n_members + 1)],
        "last_name": [f"Sample{i}" for i in range(1, n_members + 1)],
        "email": [f"member{i}@example.test" for i in range(1, n_members + 1)],
        "phone": [f"555-{1000 + (i % 9000):04d}" for i in range(1, n_members + 1)],
        "member_tier": member_tier,
        "home_market": home_market,
        "member_since_date": pd.to_datetime(member_since).date,
        "engagement_seed": engagement.round(4),
        "active_flag": 1,
        "updated_at": end,
    })
    _save(members, "members")

    campaign_ids = _id("C", 12, 3)
    campaigns = pd.DataFrame({
        "campaign_id": campaign_ids,
        "campaign_name": [f"Campaign {i}" for i in range(1, 13)],
        "channel": ["Paid Search", "Email", "Social", "Affiliate"] * 3,
        "target_market": list(resorts["market"]) + ["Orlando", "Miami", "Las Vegas", "New York"],
        "start_date": pd.date_range("2024-01-01", periods=12, freq="45D").date,
        "end_date": (pd.date_range("2024-01-01", periods=12, freq="45D") + pd.Timedelta(days=150)).date,
        "budget": rng.integers(45000, 180000, 12).astype(float),
        "updated_at": end,
    })
    _save(campaigns, "campaigns")

    n_reservations = 28000
    reservation_ids = _id("RSV", n_reservations, 7)
    member_index = rng.integers(0, n_members, n_reservations)
    resort_index = rng.integers(0, len(resorts), n_reservations)
    lead_days = rng.integers(3, 180, n_reservations)
    candidate_days = pd.date_range(start + pd.Timedelta(days=10), end, freq="D")
    day_of_year = candidate_days.dayofyear.to_numpy()
    weekend = (candidate_days.dayofweek >= 4).astype(float)
    check_in_values = np.empty(n_reservations, dtype="datetime64[ns]")
    phases = np.array([0.3, 0.8, 1.5, 2.1, 2.6, 3.0, 3.7, 4.2])
    for resort_number in range(len(resorts)):
        mask = resort_index == resort_number
        count = int(mask.sum())
        season = 1.0 + 0.45 * np.sin(2 * np.pi * day_of_year / 365.25 + phases[resort_number])
        shoulder = 1.0 + 0.15 * np.cos(4 * np.pi * day_of_year / 365.25 + phases[resort_number] / 2)
        holiday = np.where(np.isin(candidate_days.month, [3, 6, 7, 12]), 1.18, 1.0)
        weights = np.clip(season * shoulder * holiday * (1.0 + 0.10 * weekend), 0.05, None)
        weights /= weights.sum()
        check_in_values[mask] = rng.choice(candidate_days.to_numpy(), size=count, replace=True, p=weights)

    check_in = pd.DatetimeIndex(check_in_values)
    booking_dates = check_in - pd.to_timedelta(lead_days, unit="D")
    booking_dates = pd.DatetimeIndex(np.maximum(booking_dates.to_numpy(), np.datetime64(start)))
    nights = rng.integers(2, 8, n_reservations)
    check_out = check_in + pd.to_timedelta(nights, unit="D")
    statuses = rng.choice(["BOOKED", "COMPLETED", "CANCELLED", "IN_HOUSE"], n_reservations, p=[0.10, 0.76, 0.11, 0.03])
    points_used = np.maximum(0, nights * rng.integers(800, 1800, n_reservations)).astype(int)
    base_rates = np.array([240, 310, 220, 195, 215, 330, 295, 360])
    revenue = (base_rates[resort_index] * nights * rng.normal(1.0, 0.14, n_reservations)).round(2)
    revenue = np.where(statuses == "CANCELLED", 0, revenue)
    reservations = pd.DataFrame({
        "reservation_id": reservation_ids,
        "member_id": np.array(member_ids)[member_index],
        "resort_id": resorts["resort_id"].to_numpy()[resort_index],
        "booking_date": booking_dates.date,
        "check_in_date": check_in.date,
        "check_out_date": check_out.date,
        "reservation_status": statuses,
        "room_nights": nights,
        "points_redeemed": points_used,
        "net_room_revenue": revenue,
        "updated_at": pd.Series(check_out).clip(upper=end),
    })
    _save(reservations, "reservations")

    stays = reservations[reservations["reservation_status"].isin(["BOOKED", "COMPLETED", "IN_HOUSE"])].copy()
    stays.insert(0, "stay_id", _id("STY", len(stays), 7))
    stays = stays.rename(columns={"reservation_status": "stay_status"})
    stays["updated_at"] = end
    _save(stays, "resort_stays")

    point_rows: list[tuple] = []
    transaction_counter = 1
    for index, member_id in enumerate(member_ids):
        activity = int(3 + engagement[index] * 15)
        transaction_dates = start + pd.to_timedelta(rng.integers(0, (end - start).days + 1, activity), unit="D")
        for transaction_date in transaction_dates:
            transaction_type = rng.choice(["EARN", "REDEEM", "EXPIRE", "ADJUST"], p=[0.42, 0.38, 0.12, 0.08])
            amount = int(rng.integers(500, 12000))
            if transaction_type in {"REDEEM", "EXPIRE"}:
                amount *= -1
            point_rows.append((f"PTX{transaction_counter:08d}", member_id, transaction_date.date(), transaction_type, amount, transaction_date))
            transaction_counter += 1
    points = pd.DataFrame(point_rows, columns=["transaction_id", "member_id", "transaction_date", "transaction_type", "points_amount", "updated_at"])
    _save(points, "points_transactions")

    n_packages = 2600
    package_ids = _id("PKG", n_packages, 7)
    prospect_ids = _id("P", n_packages, 7)
    sale_dates = start + pd.to_timedelta(rng.integers(0, (end - start).days - 30, n_packages), unit="D")
    campaign_index = rng.integers(0, len(campaigns), n_packages)
    packages = pd.DataFrame({
        "package_id": package_ids,
        "prospect_id": prospect_ids,
        "campaign_id": campaigns["campaign_id"].to_numpy()[campaign_index],
        "lead_channel": campaigns["channel"].to_numpy()[campaign_index],
        "market": campaigns["target_market"].to_numpy()[campaign_index],
        "package_sale_date": sale_dates.date,
        "package_value": rng.integers(299, 1799, n_packages).astype(float),
        "package_status": rng.choice(["ACTIVE", "USED", "EXPIRED", "CANCELLED"], n_packages, p=[0.16, 0.62, 0.16, 0.06]),
        "updated_at": sale_dates + pd.to_timedelta(rng.integers(0, 40, n_packages), unit="D"),
    })
    _save(packages, "vacation_packages")

    tour_rows: list[tuple] = []
    contract_rows: list[tuple] = []
    touch_rows: list[tuple] = []
    tour_counter = contract_counter = touch_counter = 1
    for _, row in packages.iterrows():
        for _ in range(int(rng.integers(1, 5))):
            touch_time = pd.Timestamp(row.package_sale_date) - pd.Timedelta(days=int(rng.integers(0, 45)), hours=int(rng.integers(0, 24)))
            touch_rows.append((f"MT{touch_counter:08d}", row.prospect_id, None, row.campaign_id, row.lead_channel, touch_time, row.market, touch_time))
            touch_counter += 1
        if rng.random() < 0.82:
            tour_date = pd.Timestamp(row.package_sale_date) + pd.Timedelta(days=int(rng.integers(5, 120)))
            show_probability = 0.54 + (0.08 if row.lead_channel == "Email" else 0) + (0.05 if row.package_value > 900 else 0)
            showed = rng.random() < min(show_probability, 0.85)
            tour_status = "SHOW" if showed else rng.choice(["NO_SHOW", "CANCELLED"], p=[0.7, 0.3])
            tour_rows.append((f"TR{tour_counter:08d}", row.package_id, row.prospect_id, tour_date.date(), tour_status, row.market, tour_date))
            tour_counter += 1
            if showed:
                close_probability = 0.20 + 0.07 * (row.package_value > 900) + 0.04 * (row.lead_channel == "Paid Search")
                signed = rng.random() < close_probability
                contract_status = "SIGNED" if signed else "DECLINED"
                contract_value = float(rng.integers(11000, 72000)) if signed else 0.0
                contract_rows.append((f"CON{contract_counter:07d}", row.package_id, row.prospect_id, tour_date.date(), contract_status, contract_value, tour_date))
                contract_counter += 1

    tours = pd.DataFrame(tour_rows, columns=["tour_id", "package_id", "prospect_id", "tour_date", "tour_status", "market", "updated_at"])
    contracts = pd.DataFrame(contract_rows, columns=["contract_id", "package_id", "prospect_id", "contract_date", "contract_status", "net_contract_value", "updated_at"])
    touches = pd.DataFrame(touch_rows, columns=["touch_id", "prospect_id", "member_id", "campaign_id", "channel", "touch_time", "market", "updated_at"])
    _save(tours, "tour_events")
    _save(contracts, "sales_contracts")
    _save(touches, "marketing_events")

    case_rows: list[tuple] = []
    case_counter = 1
    for index, member_id in enumerate(member_ids):
        case_count = rng.poisson(1.4 + (1 - engagement[index]) * 1.8)
        for _ in range(case_count):
            created = start + pd.to_timedelta(int(rng.integers(0, (end - start).days + 1)), unit="D")
            priority = rng.choice(["LOW", "MEDIUM", "HIGH", "ESCALATED"], p=[0.24, 0.48, 0.20, 0.08])
            resolution = int(rng.integers(1, 240))
            case_rows.append((f"SC{case_counter:08d}", member_id, created, priority, resolution, rng.choice(["CLOSED", "OPEN"], p=[0.94, 0.06]), created + pd.Timedelta(hours=resolution)))
            case_counter += 1
    cases = pd.DataFrame(case_rows, columns=["case_id", "member_id", "case_created_at", "case_priority", "resolution_hours", "case_status", "updated_at"])
    _save(cases, "service_cases")

    labor_rows: list[tuple] = []
    shift_counter = 1
    days = pd.date_range(start, end, freq="D")
    stay_daily = reservations[reservations.reservation_status != "CANCELLED"].groupby(["resort_id", "check_in_date"]).size().to_dict()
    for _, resort in resorts.iterrows():
        for day in days:
            arrivals = stay_daily.get((resort.resort_id, day.date()), 0)
            shift_count = max(2, int(3 + arrivals * 0.9 + rng.normal(0, 1.2)))
            for _ in range(shift_count):
                hours = float(np.clip(rng.normal(7.7, 1.2), 4.0, 10.0))
                rate = float(rng.choice([18.5, 21.0, 24.0, 29.0, 35.0], p=[0.20, 0.34, 0.26, 0.15, 0.05]))
                labor_rows.append((f"LS{shift_counter:09d}", resort.resort_id, f"E{rng.integers(1, 500):05d}", day.date(), round(hours, 2), round(hours * rate, 2), day))
                shift_counter += 1
    labor = pd.DataFrame(labor_rows, columns=["shift_id", "resort_id", "employee_id", "work_date", "labor_hours", "payroll_cost", "updated_at"])
    _save(labor, "labor_shifts")

    return {
        "members": len(members), "resorts": len(resorts), "campaigns": len(campaigns),
        "reservations": len(reservations), "stays": len(stays), "points_transactions": len(points),
        "vacation_packages": len(packages), "tour_events": len(tours), "sales_contracts": len(contracts),
        "marketing_events": len(touches), "service_cases": len(cases), "labor_shifts": len(labor),
    }
