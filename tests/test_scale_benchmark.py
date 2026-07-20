from pathlib import Path

import pytest

from benchmarks.lakehouse_scale.benchmark import (
    LARGE_RUN_CONFIRMATION,
    build_plan,
    load_config,
    plan_as_dict,
    validate_destination,
)

CONFIG = Path("benchmarks/lakehouse_scale/configs/profiles.yml")


def test_profiles_have_exact_supported_sizes() -> None:
    config = load_config(CONFIG)
    assert config["profiles"]["sample"]["target_logical_bytes"] == 64 * 1024**2
    assert config["profiles"]["100gb"]["target_logical_bytes"] == 100 * 1024**3
    assert config["profiles"]["1tb"]["target_logical_bytes"] == 1024**4
    assert config["profiles"]["10tb"]["target_logical_bytes"] == 10 * 1024**4


def test_10tb_plan_is_partitioned_and_internally_consistent() -> None:
    config = load_config(CONFIG)
    plan = build_plan("10tb", config)
    payload = plan_as_dict(plan)

    assert plan.total_output_partitions == 40_960
    assert sum(domain.target_logical_bytes for domain in plan.domains) == plan.target_logical_bytes
    assert sum(domain.output_partitions for domain in plan.domains) == plan.total_output_partitions
    assert payload["estimated_total_rows"] > 1_000_000_000
    assert {domain.domain for domain in plan.domains} == set(config["domains"])


def test_sample_plan_needs_no_cloud_confirmation() -> None:
    config = load_config(CONFIG)
    validate_destination("sample", "./benchmark-output", None, config)


@pytest.mark.parametrize("profile", ["100gb", "1tb", "10tb"])
def test_large_profiles_reject_local_output(profile: str) -> None:
    config = load_config(CONFIG)
    with pytest.raises(ValueError, match="approved remote"):
        validate_destination(
            profile,
            "./benchmark-output",
            LARGE_RUN_CONFIRMATION,
            config,
        )


@pytest.mark.parametrize("profile", ["100gb", "1tb", "10tb"])
def test_large_profiles_require_explicit_cost_confirmation(profile: str) -> None:
    config = load_config(CONFIG)
    with pytest.raises(ValueError, match="requires --confirm-large-run"):
        validate_destination(
            profile,
            "abfss://benchmark@example.dfs.core.windows.net/hospitality",
            None,
            config,
        )


def test_large_profile_accepts_unity_catalog_volume() -> None:
    config = load_config(CONFIG)
    validate_destination(
        "10tb",
        "/Volumes/hospitality_benchmark/scale/raw",
        LARGE_RUN_CONFIRMATION,
        config,
    )
