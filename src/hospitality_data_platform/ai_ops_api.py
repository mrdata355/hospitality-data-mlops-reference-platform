from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .ai_ops import (
    IncidentSignal,
    IncidentType,
    SecurityPolicyViolation,
    build_default_orchestrator,
    to_primitive,
)

app = FastAPI(
    title="Hospitality AI Operations Control Plane",
    description=(
        "Policy-governed incident analysis with provider routing, tool permissions, "
        "human approval, audit evidence, and credential-free deterministic operation."
    ),
    version="2.0.0",
)
_orchestrator = build_default_orchestrator()


class IncidentRequest(BaseModel):
    incident_id: str = Field(min_length=3, max_length=100)
    incident_type: IncidentType
    metrics: dict[str, float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    untrusted_text: str = Field(default="", max_length=10_000)


class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=3, max_length=200)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hospitality-ai-operations", "version": "2.0.0"}


@app.get("/providers")
def providers() -> dict[str, object]:
    return _orchestrator.gateway.status()


@app.get("/tools")
def tools() -> dict[str, dict[str, Any]]:
    return _orchestrator.tools.catalog()


@app.post("/incidents/analyze")
def analyze_incident(payload: IncidentRequest) -> dict[str, Any]:
    try:
        report = _orchestrator.analyze(
            IncidentSignal(
                incident_id=payload.incident_id,
                incident_type=payload.incident_type,
                metrics=payload.metrics,
                metadata=payload.metadata,
                untrusted_text=payload.untrusted_text,
            )
        )
    except SecurityPolicyViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_primitive(report)


@app.get("/incidents/{report_id}")
def get_incident(report_id: str) -> dict[str, Any]:
    try:
        return to_primitive(_orchestrator.get_report(report_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{report_id}/approve")
def approve_incident(report_id: str, payload: ApprovalRequest) -> dict[str, Any]:
    try:
        return _orchestrator.execute_approved_action(report_id, payload.approved_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
