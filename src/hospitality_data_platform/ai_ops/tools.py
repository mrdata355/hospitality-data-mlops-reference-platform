from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .models import ActionRisk, AgentRole, Evidence, ToolCall


class UnauthorizedToolAccess(RuntimeError):
    pass


class ApprovalRequired(RuntimeError):
    pass


ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    allowed_roles: frozenset[AgentRole]
    action_risk: ActionRisk
    requires_approval: bool
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def invoke(
        self,
        actor: AgentRole,
        tool_name: str,
        payload: Mapping[str, Any],
        *,
        approved_by: str | None = None,
    ) -> tuple[Evidence, ToolCall]:
        try:
            spec = self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc
        if actor not in spec.allowed_roles:
            raise UnauthorizedToolAccess(f"{actor.value} cannot invoke {tool_name}")
        if spec.requires_approval and not approved_by:
            raise ApprovalRequired(f"{tool_name} requires explicit human approval")

        result = dict(spec.handler(payload))
        evidence = Evidence(source=tool_name, summary=spec.description, values=result)
        call = ToolCall(
            tool_name=tool_name,
            actor=actor,
            outcome="executed",
            action_risk=spec.action_risk,
            approval_required=spec.requires_approval,
            approved_by=approved_by,
        )
        return evidence, call

    def catalog(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "description": spec.description,
                "allowed_roles": sorted(role.value for role in spec.allowed_roles),
                "action_risk": spec.action_risk.value,
                "requires_approval": spec.requires_approval,
            }
            for name, spec in sorted(self._tools.items())
        }


def _forecast_metrics(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    wape = float(payload.get("wape", 0.0))
    baseline = float(payload.get("baseline_wape", 0.0))
    return {
        "wape": wape,
        "baseline_wape": baseline,
        "wape_delta": round(wape - baseline, 6),
        "candidate_passed": wape <= baseline and wape <= 0.30,
        "affected_resorts": payload.get("affected_resorts", []),
    }


def _quality_results(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    freshness = float(payload.get("reservation_freshness_minutes", 0.0))
    return {
        "reservation_freshness_minutes": freshness,
        "freshness_slo_minutes": 15.0,
        "freshness_breached": freshness > 15.0,
        "failed_checks": payload.get("failed_checks", []),
        "duplicate_rate": float(payload.get("duplicate_rate", 0.0)),
    }


def _lineage_lookup(_: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "critical_path": [
            "bronze.reservations",
            "silver.reservations",
            "features.waterfall_resort_week_features",
            "gold.waterfall_forecast_resort_week",
        ],
        "owner": "data-platform",
        "upstream_source": "reservation-operational-feed",
    }


def _runbook_lookup(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    incident_type = str(payload.get("incident_type", "FORECAST_DEGRADATION"))
    runbooks = {
        "FORECAST_DEGRADATION": {
            "runbook": "RB-FORECAST-001",
            "steps": [
                "Freeze candidate promotion",
                "Verify source and feature freshness",
                "Compare champion and seasonal baseline",
                "Replay affected partitions after repair",
                "Require approval before rollback",
            ],
        },
        "PIPELINE_FAILURE": {
            "runbook": "RB-DATA-002",
            "steps": [
                "Stop downstream publication",
                "Identify first failed contract",
                "Repair or quarantine source data",
                "Replay idempotently",
            ],
        },
        "SERVING_DEGRADATION": {
            "runbook": "RB-SERVING-003",
            "steps": [
                "Check readiness and error budget",
                "Shift traffic to healthy revision",
                "Preserve evidence",
                "Require approval before rollback",
            ],
        },
    }
    return runbooks.get(incident_type, runbooks["FORECAST_DEGRADATION"])


def _model_registry(_: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "registered_model": "hospitality_data_platform.models.waterfall_forecast",
        "champion_version": "18",
        "candidate_version": "19",
        "previous_stable_version": "17",
        "candidate_status": "blocked",
    }


def _serving_metrics(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "availability": float(payload.get("availability", 1.0)),
        "p95_latency_ms": float(payload.get("p95_latency_ms", 0.0)),
        "error_rate": float(payload.get("error_rate", 0.0)),
    }


def _rollback_model(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "status": "executed",
        "target_version": str(payload.get("target_version", "17")),
        "reason": str(payload.get("reason", "approved incident rollback")),
    }


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="forecast_metrics",
            description="Validated forecast acceptance, baseline, and segment evidence.",
            allowed_roles=frozenset({AgentRole.FORECAST_OPERATIONS, AgentRole.INCIDENT_COMMANDER}),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_forecast_metrics,
        )
    )
    registry.register(
        ToolSpec(
            name="quality_results",
            description="Current data quality, freshness, and duplicate-control evidence.",
            allowed_roles=frozenset({AgentRole.DATA_RELIABILITY, AgentRole.INCIDENT_COMMANDER}),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_quality_results,
        )
    )
    registry.register(
        ToolSpec(
            name="lineage_lookup",
            description="Governed upstream-to-downstream lineage path for the affected data product.",
            allowed_roles=frozenset(
                {AgentRole.FORECAST_OPERATIONS, AgentRole.DATA_RELIABILITY, AgentRole.INCIDENT_COMMANDER}
            ),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_lineage_lookup,
        )
    )
    registry.register(
        ToolSpec(
            name="runbook_lookup",
            description="Approved operational response procedure for the incident class.",
            allowed_roles=frozenset(
                {AgentRole.FORECAST_OPERATIONS, AgentRole.DATA_RELIABILITY, AgentRole.INCIDENT_COMMANDER}
            ),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_runbook_lookup,
        )
    )
    registry.register(
        ToolSpec(
            name="model_registry",
            description="Read-only model aliases and immutable version history.",
            allowed_roles=frozenset({AgentRole.FORECAST_OPERATIONS, AgentRole.INCIDENT_COMMANDER}),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_model_registry,
        )
    )
    registry.register(
        ToolSpec(
            name="serving_metrics",
            description="Serving availability, latency, and error-budget evidence.",
            allowed_roles=frozenset({AgentRole.INCIDENT_COMMANDER}),
            action_risk=ActionRisk.LOW,
            requires_approval=False,
            handler=_serving_metrics,
        )
    )
    registry.register(
        ToolSpec(
            name="rollback_model",
            description="Move the production alias to a previously validated immutable model version.",
            allowed_roles=frozenset({AgentRole.INCIDENT_COMMANDER}),
            action_risk=ActionRisk.HIGH,
            requires_approval=True,
            handler=_rollback_model,
        )
    )
    return registry
