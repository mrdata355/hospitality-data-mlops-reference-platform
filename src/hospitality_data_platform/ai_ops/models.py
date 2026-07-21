from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class AgentRole(str, Enum):
    FORECAST_OPERATIONS = "forecast_operations_analyst"
    DATA_RELIABILITY = "data_reliability_investigator"
    INCIDENT_COMMANDER = "incident_commander"
    MEMBER_RISK = "member_risk_analyst"


class ActionRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class IncidentType(str, Enum):
    FORECAST_DEGRADATION = "FORECAST_DEGRADATION"
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    SERVING_DEGRADATION = "SERVING_DEGRADATION"
    PROMPT_INJECTION = "PROMPT_INJECTION"


class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    name: str
    model: str
    priority: int
    capabilities: frozenset[str]
    allowed_classifications: frozenset[DataClassification]
    input_cost_per_1k: float
    output_cost_per_1k: float
    nominal_latency_ms: int
    failure_threshold: int = 1
    cooldown_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    prompt: str
    workflow: str
    data_classification: DataClassification = DataClassification.INTERNAL
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    max_cost_usd: float = 0.25
    max_latency_ms: int = 5_000
    estimated_completion_tokens: int = 250
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    model: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cost_usd: float
    route_reason: str
    trace_id: str


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor: str
    outcome: str
    details: Mapping[str, Any]
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ToolCall:
    tool_name: str
    actor: AgentRole
    outcome: str
    action_risk: ActionRisk
    approval_required: bool
    approved_by: str | None = None


@dataclass(frozen=True, slots=True)
class Evidence:
    source: str
    summary: str
    values: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class AgentResult:
    role: AgentRole
    objective: str
    summary: str
    findings: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    recommended_action: str
    action_risk: ActionRisk
    approval_required: bool
    tool_calls: tuple[ToolCall, ...]
    provider_trace_id: str | None
    provider: str | None


@dataclass(frozen=True, slots=True)
class IncidentSignal:
    incident_id: str
    incident_type: IncidentType
    metrics: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    untrusted_text: str = ""


@dataclass(frozen=True, slots=True)
class IncidentReport:
    report_id: str
    incident_id: str
    severity: Severity
    status: str
    executive_summary: str
    root_cause: str
    recommended_action: str
    approval_required: bool
    approval_action: str | None
    agents: tuple[AgentResult, ...]
    routing_trace: tuple[Mapping[str, Any], ...]
    audit_events: tuple[AuditEvent, ...]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return to_primitive(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [to_primitive(item) for item in value]
    return value
