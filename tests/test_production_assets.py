from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_reference_disclaimer_is_prominent():
    readme = (ROOT / "README.md").read_text().lower()
    assert "independent reference implementation" in readme
    assert "does not represent an approved or deployed production system" in readme


def test_databricks_targets_have_isolated_catalogs():
    bundle = yaml.safe_load((ROOT / "databricks/databricks.yml").read_text())
    catalogs = {name: cfg["variables"]["catalog"] for name, cfg in bundle["targets"].items()}
    assert len(set(catalogs.values())) == len(catalogs)


def test_workflow_builds_features_before_training_and_promotion():
    workflow = yaml.safe_load((ROOT / "databricks/resources/jobs.yml").read_text())
    tasks = workflow["resources"]["jobs"]["hospitality_data_platform_pipeline"]["tasks"]
    by_key = {task["task_key"]: task for task in tasks}
    assert {item["task_key"] for item in by_key["train_waterfall"]["depends_on"]} == {
        "build_waterfall_features"
    }
    assert {item["task_key"] for item in by_key["batch_score"]["depends_on"]} == {
        "promote_waterfall"
    }


def test_kubernetes_has_scalability_and_resilience_controls():
    deployment = yaml.safe_load((ROOT / "k8s/deployment.yaml").read_text())
    hpa = yaml.safe_load((ROOT / "k8s/hpa.yaml").read_text())
    assert deployment["spec"]["replicas"] >= 3
    assert deployment["spec"]["strategy"]["rollingUpdate"]["maxUnavailable"] == 0
    assert deployment["spec"]["template"]["spec"]["topologySpreadConstraints"]
    assert hpa["spec"]["maxReplicas"] >= 10
    assert (ROOT / "k8s/pdb.yaml").exists()
    assert (ROOT / "k8s/networkpolicy.yaml").exists()


def test_platform_governance_and_scalability_docs_exist():
    required = [
        "docs/CAPABILITY_MATRIX.md",
        "docs/SYSTEM_VALIDATION_WALKTHROUGH.md",
        "docs/SCALABILITY_STRATEGY.md",
        "docs/MODEL_GOVERNANCE.md",
        "docs/THREAT_MODEL.md",
        "docs/CAPACITY_AND_LOAD_PLAN.md",
    ]
    for path in required:
        assert (ROOT / path).exists(), path
