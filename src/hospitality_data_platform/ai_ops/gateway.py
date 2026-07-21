from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .models import (
    AuditEvent,
    DataClassification,
    ProviderConfig,
    ProviderRequest,
    ProviderResponse,
    to_primitive,
)
from .security import PromptInjectionGuard, SensitiveDataRedactor


class ProviderError(RuntimeError):
    pass


class ProviderUnavailable(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int
    cooldown_seconds: float
    failures: int = 0
    state: CircuitState = CircuitState.CLOSED
    opened_at: float | None = None

    def allow_request(self) -> bool:
        if self.state is CircuitState.CLOSED:
            return True
        if self.state is CircuitState.OPEN and self.opened_at is not None:
            if time.monotonic() - self.opened_at >= self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
        return self.state is CircuitState.HALF_OPEN

    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()

    def snapshot(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
        }


class BudgetLedger:
    def __init__(self, workflow_limits: dict[str, float] | None = None, default_limit: float = 1.0):
        self._limits = workflow_limits or {}
        self._default_limit = default_limit
        self._spent: dict[str, float] = {}
        self._lock = threading.Lock()

    def ensure_available(self, workflow: str, estimated_cost: float) -> None:
        with self._lock:
            limit = self._limits.get(workflow, self._default_limit)
            spent = self._spent.get(workflow, 0.0)
            if spent + estimated_cost > limit:
                raise BudgetExceeded(
                    f"Workflow budget exceeded for {workflow}: "
                    f"spent={spent:.6f}, requested={estimated_cost:.6f}, limit={limit:.6f}"
                )

    def record(self, workflow: str, actual_cost: float) -> None:
        with self._lock:
            self._spent[workflow] = self._spent.get(workflow, 0.0) + actual_cost

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            workflows = set(self._limits) | set(self._spent)
            return {
                workflow: {
                    "spent_usd": round(self._spent.get(workflow, 0.0), 8),
                    "limit_usd": self._limits.get(workflow, self._default_limit),
                }
                for workflow in sorted(workflows)
            }


class Provider(Protocol):
    config: ProviderConfig

    def complete(self, request: ProviderRequest, trace_id: str) -> ProviderResponse: ...


class DeterministicProvider:
    """Credential-free provider used for CI, demos, and failure-injection tests."""

    def __init__(self, config: ProviderConfig, failures_before_success: int = 0):
        self.config = config
        self._remaining_failures = failures_before_success

    def complete(self, request: ProviderRequest, trace_id: str) -> ProviderResponse:
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise ProviderError(f"Injected failure from {self.config.name}")

        prompt_tokens = max(1, len(request.prompt) // 4)
        completion_tokens = min(max(request.estimated_completion_tokens, 32), 512)
        cost = (
            prompt_tokens * self.config.input_cost_per_1k
            + completion_tokens * self.config.output_cost_per_1k
        ) / 1_000
        digest = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()[:12]
        content = json.dumps(
            {
                "workflow": request.workflow,
                "analysis_id": digest,
                "status": "completed",
                "grounding": "tool-evidence-only",
                "provider": self.config.name,
            },
            sort_keys=True,
        )
        return ProviderResponse(
            provider=self.config.name,
            model=self.config.model,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=float(self.config.nominal_latency_ms),
            cost_usd=round(cost, 8),
            route_reason="highest-ranked eligible healthy provider",
            trace_id=trace_id,
        )


class LLMGateway:
    def __init__(
        self,
        providers: Iterable[Provider],
        budget_ledger: BudgetLedger | None = None,
        guard: PromptInjectionGuard | None = None,
        redactor: SensitiveDataRedactor | None = None,
    ) -> None:
        self._providers = {provider.config.name: provider for provider in providers}
        self._breakers = {
            provider.config.name: CircuitBreaker(
                failure_threshold=provider.config.failure_threshold,
                cooldown_seconds=provider.config.cooldown_seconds,
            )
            for provider in providers
        }
        self._budget = budget_ledger or BudgetLedger()
        self._guard = guard or PromptInjectionGuard()
        self._redactor = redactor or SensitiveDataRedactor()
        self._audit: list[AuditEvent] = []
        self._routing_trace: list[dict[str, object]] = []

    def _eligible(self, request: ProviderRequest) -> list[Provider]:
        candidates = []
        for provider in self._providers.values():
            config = provider.config
            if request.data_classification not in config.allowed_classifications:
                continue
            if not request.required_capabilities.issubset(config.capabilities):
                continue
            if config.nominal_latency_ms > request.max_latency_ms:
                continue
            candidates.append(provider)
        return sorted(
            candidates,
            key=lambda item: (
                item.config.priority,
                item.config.input_cost_per_1k + item.config.output_cost_per_1k,
                item.config.nominal_latency_ms,
            ),
        )

    @staticmethod
    def _estimate_cost(config: ProviderConfig, request: ProviderRequest) -> float:
        prompt_tokens = max(1, len(request.prompt) // 4)
        return (
            prompt_tokens * config.input_cost_per_1k
            + request.estimated_completion_tokens * config.output_cost_per_1k
        ) / 1_000

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self._guard.enforce(request.prompt)
        sanitized_metadata = self._redactor.redact_mapping(request.metadata)
        trace_id = str(uuid.uuid4())
        failures: list[str] = []

        candidates = self._eligible(request)
        if not candidates:
            raise ProviderUnavailable(
                "No provider satisfies classification, capability, and latency policy."
            )

        for provider in candidates:
            name = provider.config.name
            breaker = self._breakers[name]
            if not breaker.allow_request():
                failures.append(f"{name}: circuit open")
                self._routing_trace.append(
                    {"trace_id": trace_id, "provider": name, "outcome": "skipped_circuit_open"}
                )
                continue

            estimated_cost = self._estimate_cost(provider.config, request)
            if estimated_cost > request.max_cost_usd:
                failures.append(f"{name}: request cost ceiling")
                self._routing_trace.append(
                    {"trace_id": trace_id, "provider": name, "outcome": "skipped_cost_ceiling"}
                )
                continue
            try:
                self._budget.ensure_available(request.workflow, estimated_cost)
                response = provider.complete(request, trace_id)
            except BudgetExceeded:
                raise
            except ProviderError as exc:
                breaker.record_failure()
                failures.append(f"{name}: {exc}")
                self._routing_trace.append(
                    {"trace_id": trace_id, "provider": name, "outcome": "provider_failure"}
                )
                self._audit.append(
                    AuditEvent(
                        event_type="provider_call",
                        actor="llm_gateway",
                        outcome="failed",
                        details={"provider": name, "workflow": request.workflow},
                    )
                )
                continue

            breaker.record_success()
            self._budget.record(request.workflow, response.cost_usd)
            self._routing_trace.append(
                {
                    "trace_id": trace_id,
                    "provider": name,
                    "model": provider.config.model,
                    "outcome": "success",
                    "cost_usd": response.cost_usd,
                    "metadata": sanitized_metadata,
                }
            )
            self._audit.append(
                AuditEvent(
                    event_type="provider_call",
                    actor="llm_gateway",
                    outcome="success",
                    details={
                        "provider": name,
                        "model": provider.config.model,
                        "workflow": request.workflow,
                        "classification": request.data_classification.value,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
            return response

        raise ProviderUnavailable(
            "All eligible providers failed or were unavailable: " + "; ".join(failures)
        )

    def status(self) -> dict[str, object]:
        return {
            "providers": {
                name: {
                    "model": provider.config.model,
                    "priority": provider.config.priority,
                    "capabilities": sorted(provider.config.capabilities),
                    "allowed_classifications": sorted(
                        classification.value
                        for classification in provider.config.allowed_classifications
                    ),
                    "circuit": self._breakers[name].snapshot(),
                }
                for name, provider in sorted(self._providers.items())
            },
            "budgets": self._budget.snapshot(),
        }

    @property
    def audit_events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._audit)

    @property
    def routing_trace(self) -> tuple[dict[str, object], ...]:
        return tuple(to_primitive(item) for item in self._routing_trace)


def default_provider_configs() -> tuple[ProviderConfig, ProviderConfig]:
    common_classifications = frozenset(
        {
            DataClassification.PUBLIC,
            DataClassification.INTERNAL,
            DataClassification.CONFIDENTIAL,
        }
    )
    return (
        ProviderConfig(
            name="primary-enterprise-provider",
            model="enterprise-analysis-large",
            priority=1,
            capabilities=frozenset({"analysis", "structured-output", "tool-grounding"}),
            allowed_classifications=common_classifications,
            input_cost_per_1k=0.003,
            output_cost_per_1k=0.009,
            nominal_latency_ms=180,
        ),
        ProviderConfig(
            name="resilient-fallback-provider",
            model="enterprise-analysis-medium",
            priority=2,
            capabilities=frozenset({"analysis", "structured-output", "tool-grounding"}),
            allowed_classifications=common_classifications,
            input_cost_per_1k=0.0015,
            output_cost_per_1k=0.0045,
            nominal_latency_ms=240,
        ),
    )


def build_default_gateway(
    primary_failures: int = 0, workflow_budget_usd: float = 2.0
) -> LLMGateway:
    primary, fallback = default_provider_configs()
    providers = (
        DeterministicProvider(primary, failures_before_success=primary_failures),
        DeterministicProvider(fallback),
    )
    budgets = BudgetLedger(
        workflow_limits={
            "forecast-incident": workflow_budget_usd,
            "pipeline-incident": workflow_budget_usd,
            "serving-incident": workflow_budget_usd,
            "incident-command": workflow_budget_usd,
        },
        default_limit=workflow_budget_usd,
    )
    return LLMGateway(providers, budget_ledger=budgets)
