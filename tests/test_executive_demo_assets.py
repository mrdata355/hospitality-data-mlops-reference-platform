from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_executive_demo_assets_are_present() -> None:
    required = [
        "docs/EXECUTIVE_DEMO.md",
        "scripts/run_executive_demo.py",
        "scripts/run_local_executive_demo.py",
        "scripts/deploy_azure_container_app.sh",
        ".github/workflows/deploy-azure-demo.yml",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path


def test_azure_demo_workflow_is_manual_and_uses_oidc() -> None:
    workflow = (ROOT / ".github/workflows/deploy-azure-demo.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "id-token: write" in workflow
    assert "azure/login@v2" in workflow
    assert "environment: azure-demo" in workflow
    assert "synthetic" in workflow
    assert "push:" not in workflow


def test_demo_document_preserves_claim_boundaries() -> None:
    guide = (ROOT / "docs/EXECUTIVE_DEMO.md").read_text().lower()
    for phrase in (
        "generated non-production data only",
        "not a claim of real-customer predictive lift",
        "not described as a company deployment",
    ):
        assert phrase in guide
