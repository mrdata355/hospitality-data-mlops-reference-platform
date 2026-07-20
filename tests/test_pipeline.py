from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_dimensional_grains_are_unique():
    dim_member = pd.read_csv(ROOT / "data/gold/dim_member.csv")
    dim_resort = pd.read_csv(ROOT / "data/gold/dim_resort.csv")
    assert not dim_member.member_key.duplicated().any()
    assert not dim_member.member_id.duplicated().any()
    assert not dim_resort.resort_key.duplicated().any()
    assert not dim_resort.resort_id.duplicated().any()


def test_fact_stay_has_valid_foreign_keys():
    fact = pd.read_csv(ROOT / "data/gold/fact_stay.csv")
    members = set(pd.read_csv(ROOT / "data/gold/dim_member.csv").member_key)
    resorts = set(pd.read_csv(ROOT / "data/gold/dim_resort.csv").resort_key)
    assert set(fact.member_key).issubset(members)
    assert set(fact.resort_key).issubset(resorts)


def test_gold_grains():
    resort_month = pd.read_csv(ROOT / "data/gold/resort_monthly_performance.csv")
    funnel = pd.read_csv(ROOT / "data/gold/campaign_tour_sales_attribution.csv")
    assert not resort_month.duplicated(["resort_id", "month_start"]).any()
    assert not funnel.duplicated(["campaign_id", "lead_channel", "market", "month_start"]).any()
