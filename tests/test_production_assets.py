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


def test_kubernetes_has_scalability_security_and_release_controls():
    deployment = yaml.safe_load((ROOT / "k8s/deployment.yaml").read_text())
    hpa = yaml.safe_load((ROOT / "k8s/hpa.yaml").read_text())
    pod_spec = deployment["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]

    assert deployment["spec"]["replicas"] >= 3
    assert deployment["spec"]["strategy"]["rollingUpdate"]["maxUnavailable"] == 0
    assert pod_spec["topologySpreadConstraints"]
    assert pod_spec["securityContext"]["runAsUser"] == 10001
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
    assert container["image"].startswith("ghcr.io/mrdata355/")
    assert "your-registry" not in container["image"]
    assert hpa["spec"]["maxReplicas"] >= 10
    assert (ROOT / "k8s/pdb.yaml").exists()
    assert (ROOT / "k8s/networkpolicy.yaml").exists()
    assert (ROOT / "k8s/serviceaccount.yaml").exists()
    assert (ROOT / "k8s/kustomization.yaml").exists()


def test_ci_requires_a_running_container_smoke_test():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "serving-smoke:" in workflow
    assert "scripts/smoke_test_serving.py" in workflow
    assert "--read-only" in workflow
    assert "--cap-drop ALL" in workflow
    assert "validated-member-risk-model" in workflow


def test_versioned_image_release_workflow_exists():
    release_workflow = (ROOT / ".github/workflows/release-image.yml").read_text()
    assert "ghcr.io/${{ github.repository }}" in release_workflow
    assert "packages: write" in release_workflow
    assert "linux/amd64,linux/arm64" in release_workflow
    assert "provenance: mode=max" in release_workflow
    assert "sbom: true" in release_workflow


def test_platform_governance_and_scalability_docs_exist():
    required = [
        "docs/CAPABILITY_MATRIX.md",
        "docs/SYSTEM_VALIDATION_WALKTHROUGH.md",
        "docs/SCALABILITY_STRATEGY.md",
        "docs/MODEL_GOVERNANCE.md",
        "docs/THREAT_MODEL.md",
        "docs/CAPACITY_AND_LOAD_PLAN.md",
        "docs/SERVING_VALIDATION.md",
    ]
    for path in required:
        assert (ROOT / path).exists(), path
