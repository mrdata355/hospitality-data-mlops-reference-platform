from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_system_validation_assets_are_present() -> None:
    required = [
        "docs/SYSTEM_VALIDATION.md",
        "scripts/run_system_validation.py",
        "scripts/run_local_system_validation.py",
        "scripts/deploy_azure_container_app.sh",
        ".github/workflows/deploy-azure-validation.yml",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path


def test_azure_validation_workflow_is_manual_and_uses_oidc() -> None:
    workflow = (ROOT / ".github/workflows/deploy-azure-validation.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "id-token: write" in workflow
    assert "azure/login@v2" in workflow
    assert "environment: azure-validation" in workflow
    assert "generated non-production data only" in workflow
    assert "push:" not in workflow


def test_system_validation_document_preserves_claim_boundaries() -> None:
    guide = (ROOT / "docs/SYSTEM_VALIDATION.md").read_text().lower()
    for phrase in (
        "generated non-production data only",
        "not claims of real-customer predictive lift",
        "production authorization",
    ):
        assert phrase in guide
