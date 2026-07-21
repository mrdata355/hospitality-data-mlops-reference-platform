from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

from .gateway import LLMGateway
from .models import (
    ActionRisk,
    AgentResult,
    AgentRole,
    DataClassification,
    Evidence,
    IncidentSignal,
    IncidentType,
    ProviderRequest,
    Severity,
    ToolCall,
)
from .tools import ToolRegistry


@dataclass(slots=True)
class ForecastOperationsAgent:
    gateway: LLMGateway
    tools: ToolRegistry
    role: AgentRole = AgentRole.FORECAST_OPERATIONS

    def run(self, signal: IncidentSignal) -> AgentResult:
        metrics_payload = {
            **signal.metrics,
            "affected_resorts": signal.metadata.get("affected_resorts", []),
        }
        evidence: list[Evidence] = []
        calls: list[ToolCall] = []
        for name, payload in (
            ("forecast_metrics", metrics_payload),
            ("lineage_lookup", {}),
            ("model_registry", {}),
            ("runbook_lookup", {"incident_type": signal.incident_type.value}),
        ):
            item, call = self.tools.invoke(self.role, name, payload)
            evidence.append(item)
            calls.append(call)

        wape = float(signal.metrics.get("wape", 0.0))
        baseline = float(signal.metrics.get("baseline_wape", 0.0))
        freshness = float(signal.metrics.get("reservation_freshness_minutes", 0.0))
        findings = [
            f"Candidate WAPE is {wape:.3f} versus baseline {baseline:.3f}.",
            f"Reservation freshness is {freshness:.1f} minutes against a 15-minute SLO.",
        ]
        if freshness > 15:
            findings.append("The feature build consumed stale reservation inputs.")
        if wape > baseline:
            findings.append("The candidate is worse than the approved seasonal baseline.")

        prompt = json.dumps(
            {
                "objective": "Diagnose forecast degradation using only supplied tool evidence.",
                "incident_id": signal.incident_id,
                "findings": findings,
                "evidence_sources": [item.source for item in evidence],
            },
            sort_keys=True,
        )
        response = self.gateway.complete(
            ProviderRequest(
                prompt=prompt,
                workflow="forecast-incident",
                data_classification=DataClassification.INTERNAL,
                required_capabilities=frozenset(
                    {"analysis", "structured-output", "tool-grounding"}
                ),
                metadata={"incident_id": signal.incident_id},
            )
        )
        action = (
            "Freeze candidate promotion, repair reservation freshness, replay affected partitions, "
            "and rerun chronological validation."
            if freshness > 15
            else "Freeze candidate promotion and rerun baseline comparison before release."
        )
        return AgentResult(
            role=self.role,
            objective="Diagnose resort-week forecast degradation.",
            summary=(
                "Forecast quality failed release controls and requires evidence-based remediation."
            ),
            findings=tuple(findings),
            evidence=tuple(evidence),
            recommended_action=action,
            action_risk=ActionRisk.MEDIUM,
            approval_required=False,
            tool_calls=tuple(calls),
            provider_trace_id=response.trace_id,
            provider=response.provider,
        )


@dataclass(slots=True)
class DataReliabilityAgent:
    gateway: LLMGateway
    tools: ToolRegistry
    role: AgentRole = AgentRole.DATA_RELIABILITY

    def run(self, signal: IncidentSignal) -> AgentResult:
        payload = {
            **signal.metrics,
            "failed_checks": signal.metadata.get("failed_checks", []),
        }
        evidence: list[Evidence] = []
        calls: list[ToolCall] = []
        for name, tool_payload in (
            ("quality_results", payload),
            ("lineage_lookup", {}),
            ("runbook_lookup", {"incident_type": signal.incident_type.value}),
        ):
            item, call = self.tools.invoke(self.role, name, tool_payload)
            evidence.append(item)
            calls.append(call)

        freshness = float(signal.metrics.get("reservation_freshness_minutes", 0.0))
        duplicate_rate = float(signal.metrics.get("duplicate_rate", 0.0))
        findings = [
            f"Reservation freshness measured {freshness:.1f} minutes.",
            f"Duplicate rate measured {duplicate_rate:.4f}.",
            "Lineage places the freshness breach upstream of the resort-week feature table.",
        ]
        prompt = json.dumps(
            {
                "objective": "Identify the first broken data contract from governed evidence.",
                "incident_id": signal.incident_id,
                "findings": findings,
                "evidence_sources": [item.source for item in evidence],
            },
            sort_keys=True,
        )
        response = self.gateway.complete(
            ProviderRequest(
                prompt=prompt,
                workflow="pipeline-incident",
                data_classification=DataClassification.INTERNAL,
                required_capabilities=frozenset(
                    {"analysis", "structured-output", "tool-grounding"}
                ),
                metadata={"incident_id": signal.incident_id},
            )
        )
        return AgentResult(
            role=self.role,
            objective="Identify the earliest failed data contract and blast radius.",
            summary="The reservation feed breached freshness controls before feature publication.",
            findings=tuple(findings),
            evidence=tuple(evidence),
            recommended_action=(
                "Quarantine stale partitions, repair ingestion, and replay idempotently."
            ),
            action_risk=ActionRisk.MEDIUM,
            approval_required=False,
            tool_calls=tuple(calls),
            provider_trace_id=response.trace_id,
            provider=response.provider,
        )


@dataclass(slots=True)
class IncidentCommander:
    gateway: LLMGateway
    tools: ToolRegistry
    role: AgentRole = AgentRole.INCIDENT_COMMANDER

    def assess(
        self, signal: IncidentSignal, agent_results: Iterable[AgentResult]
    ) -> dict[str, object]:
        evidence: list[Evidence] = []
        calls: list[ToolCall] = []
        for name, payload in (
            ("runbook_lookup", {"incident_type": signal.incident_type.value}),
            ("model_registry", {}),
        ):
            item, call = self.tools.invoke(self.role, name, payload)
            evidence.append(item)
            calls.append(call)

        if signal.incident_type is IncidentType.SERVING_DEGRADATION:
            item, call = self.tools.invoke(self.role, "serving_metrics", signal.metrics)
            evidence.append(item)
            calls.append(call)

        results = tuple(agent_results)
        wape = float(signal.metrics.get("wape", 0.0))
        baseline = float(signal.metrics.get("baseline_wape", 0.0))
        availability = float(signal.metrics.get("availability", 1.0))
        freshness = float(signal.metrics.get("reservation_freshness_minutes", 0.0))

        if availability < 0.95 or wape >= 0.40:
            severity = Severity.SEV1
        elif availability < 0.995 or wape > baseline or freshness > 15:
            severity = Severity.SEV2
        else:
            severity = Severity.SEV3

        rollback_recommended = wape > baseline + 0.02 or availability < 0.99
        action = (
            "Roll back to the previous validated model version after human approval, "
            "then repair and replay."
            if rollback_recommended
            else (
                "Hold promotion, repair the upstream fault, and revalidate before resuming release."
            )
        )
        root_cause = (
            "Reservation ingestion freshness breached its SLO, propagating stale lag features into "
            "the resort-week forecast candidate."
            if freshness > 15
            else "The candidate failed its baseline or serving reliability gate."
        )
        prompt = json.dumps(
            {
                "objective": "Assign severity and propose a controlled response.",
                "incident_id": signal.incident_id,
                "agent_roles": [result.role.value for result in results],
                "severity": severity.value,
                "approval_required": rollback_recommended,
                "evidence_sources": [item.source for item in evidence],
            },
            sort_keys=True,
        )
        response = self.gateway.complete(
            ProviderRequest(
                prompt=prompt,
                workflow="incident-command",
                data_classification=DataClassification.INTERNAL,
                required_capabilities=frozenset(
                    {"analysis", "structured-output", "tool-grounding"}
                ),
                metadata={"incident_id": signal.incident_id},
            )
        )
        return {
            "severity": severity,
            "root_cause": root_cause,
            "recommended_action": action,
            "approval_required": rollback_recommended,
            "approval_action": "rollback_model" if rollback_recommended else None,
            "evidence": tuple(evidence),
            "tool_calls": tuple(calls),
            "provider": response.provider,
            "provider_trace_id": response.trace_id,
        }
