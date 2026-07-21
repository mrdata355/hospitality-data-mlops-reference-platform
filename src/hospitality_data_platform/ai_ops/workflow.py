from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any

from .agents import DataReliabilityAgent, ForecastOperationsAgent, IncidentCommander
from .gateway import LLMGateway, build_default_gateway
from .models import (
    AgentResult,
    AgentRole,
    AuditEvent,
    IncidentReport,
    IncidentSignal,
    IncidentType,
)
from .security import PromptInjectionGuard
from .tools import ToolRegistry, build_default_tool_registry


class IncidentOrchestrator:
    def __init__(
        self,
        gateway: LLMGateway,
        tools: ToolRegistry,
        guard: PromptInjectionGuard | None = None,
    ):
        self.gateway = gateway
        self.tools = tools
        self.guard = guard or PromptInjectionGuard()
        self.forecast_agent = ForecastOperationsAgent(gateway, tools)
        self.reliability_agent = DataReliabilityAgent(gateway, tools)
        self.commander = IncidentCommander(gateway, tools)
        self._reports: dict[str, IncidentReport] = {}
        self._local_audit: list[AuditEvent] = []

    def analyze(self, signal: IncidentSignal) -> IncidentReport:
        self.guard.enforce(signal.untrusted_text)
        self._local_audit.append(
            AuditEvent(
                event_type="incident_received",
                actor="incident_orchestrator",
                outcome="accepted",
                details={"incident_id": signal.incident_id, "type": signal.incident_type.value},
            )
        )

        agents: list[AgentResult] = []
        if signal.incident_type in {
            IncidentType.FORECAST_DEGRADATION,
            IncidentType.PIPELINE_FAILURE,
        }:
            agents.append(self.forecast_agent.run(signal))
            agents.append(self.reliability_agent.run(signal))
        elif signal.incident_type is IncidentType.SERVING_DEGRADATION:
            agents.append(self.forecast_agent.run(signal))
        else:
            agents.append(self.reliability_agent.run(signal))

        command = self.commander.assess(signal, agents)
        report_id = str(uuid.uuid4())
        providers = sorted({result.provider for result in agents if result.provider})
        executive_summary = (
            f"{command['severity'].value} {signal.incident_type.value}: "
            f"{command['root_cause']} Providers used: {', '.join(providers)}."
        )
        report = IncidentReport(
            report_id=report_id,
            incident_id=signal.incident_id,
            severity=command["severity"],
            status="AWAITING_APPROVAL" if command["approval_required"] else "ACTIONABLE",
            executive_summary=executive_summary,
            root_cause=str(command["root_cause"]),
            recommended_action=str(command["recommended_action"]),
            approval_required=bool(command["approval_required"]),
            approval_action=command["approval_action"],
            agents=tuple(agents),
            routing_trace=self.gateway.routing_trace,
            audit_events=tuple(self._local_audit) + self.gateway.audit_events,
        )
        self._reports[report_id] = report
        return report

    def get_report(self, report_id: str) -> IncidentReport:
        try:
            return self._reports[report_id]
        except KeyError as exc:
            raise KeyError(f"Unknown report: {report_id}") from exc

    def execute_approved_action(self, report_id: str, approved_by: str) -> dict[str, Any]:
        report = self.get_report(report_id)
        if not report.approval_required or report.approval_action != "rollback_model":
            raise ValueError("The report has no pending high-risk approval action.")
        evidence, call = self.tools.invoke(
            AgentRole.INCIDENT_COMMANDER,
            "rollback_model",
            {
                "target_version": "17",
                "reason": f"Approved response for incident {report.incident_id}",
            },
            approved_by=approved_by,
        )
        approval_event = AuditEvent(
            event_type="human_approval",
            actor=approved_by,
            outcome="approved_and_executed",
            details={"report_id": report_id, "tool": call.tool_name},
        )
        updated = replace(
            report,
            status="ACTION_EXECUTED",
            audit_events=report.audit_events + (approval_event,),
        )
        self._reports[report_id] = updated
        return {
            "report_id": report_id,
            "status": updated.status,
            "action": call.tool_name,
            "approved_by": approved_by,
            "result": dict(evidence.values),
        }


def build_default_orchestrator(
    *, primary_failures: int = 0, workflow_budget_usd: float = 2.0
) -> IncidentOrchestrator:
    gateway = build_default_gateway(
        primary_failures=primary_failures,
        workflow_budget_usd=workflow_budget_usd,
    )
    return IncidentOrchestrator(gateway, build_default_tool_registry())
