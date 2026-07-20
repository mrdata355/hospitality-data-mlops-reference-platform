from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from .config import MODELS
from .models import CHURN_CATEGORICAL, CHURN_NUMERIC

MODEL_PATH = MODELS / "member_churn_model.joblib"
MODEL_SOURCE = os.getenv("MODEL_SOURCE", "local").strip().lower()
MODEL_ALIAS = os.getenv("MODEL_ALIAS", "Champion")
MODEL_URI = os.getenv(
    "MODEL_URI", "models:/hospitality_data_platform.models.member_churn_model@Champion"
)
_model: Any = None
_model_loaded_at: str | None = None
_request_count = 0
_error_count = 0
_latency_ms_total = 0.0


def _load_model() -> Any:
    global _model, _model_loaded_at
    if MODEL_SOURCE == "local":
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
    elif MODEL_SOURCE == "mlflow":
        try:
            import mlflow.pyfunc
        except ImportError as exc:
            raise RuntimeError("MLflow serving was requested, but mlflow is not installed.") from exc
        _model = mlflow.pyfunc.load_model(MODEL_URI)
    else:
        raise RuntimeError("MODEL_SOURCE must be either 'local' or 'mlflow'.")
    _model_loaded_at = datetime.now(timezone.utc).isoformat()
    return _model


@asynccontextmanager
async def lifespan(_: FastAPI):
    if MODEL_SOURCE == "mlflow" or MODEL_PATH.exists():
        _load_model()
    yield


app = FastAPI(
    title="Member Risk Scoring Service",
    description="Versioned member risk scoring API for the hospitality reference platform.",
    version="1.1.0",
    lifespan=lifespan,
)


class MemberFeatures(BaseModel):
    tenure_months: float = Field(ge=0)
    points_earned_12m: float = Field(ge=0)
    points_redeemed_12m: float = Field(ge=0)
    points_expired_12m: float = Field(ge=0)
    points_utilization_rate: float = Field(ge=0)
    expired_share: float = Field(ge=0)
    stays_12m: float = Field(ge=0)
    room_nights_12m: float = Field(ge=0)
    net_room_revenue_12m: float = Field(ge=0)
    avg_booking_lead_days_12m: float = Field(ge=0)
    service_cases_90d: float = Field(ge=0)
    escalated_cases_90d: float = Field(ge=0)
    avg_resolution_hours_90d: float = Field(ge=0)
    days_since_last_booking: float = Field(ge=0)
    member_tier: Literal["Member", "Elite", "Premier", "Max"]
    home_market: str = Field(min_length=1, max_length=100)


class ScoreResponse(BaseModel):
    churn_probability: float
    risk_band: Literal["LOW", "MEDIUM", "HIGH"]
    model_alias: str
    scored_at: str
    request_id: str


def get_model() -> Any:
    global _model
    if _model is None:
        try:
            return _load_model()
        except (FileNotFoundError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Approved model artifact is unavailable.",
            ) from exc
    return _model


def _predict_probability(model: Any, row: pd.DataFrame) -> float:
    feature_frame = row[CHURN_NUMERIC + CHURN_CATEGORICAL]
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(feature_frame)[:, 1][0])
    prediction = model.predict(feature_frame)
    if isinstance(prediction, pd.DataFrame):
        for column in ("churn_probability", "probability", "prediction"):
            if column in prediction.columns:
                return float(prediction.iloc[0][column])
        return float(prediction.iloc[0, 0])
    if isinstance(prediction, pd.Series):
        return float(prediction.iloc[0])
    array = np.asarray(prediction).reshape(-1)
    if not len(array):
        raise RuntimeError("The configured model returned no predictions.")
    return float(array[0])


@app.middleware("http")
async def request_context(request: Request, call_next):
    global _request_count, _error_count, _latency_ms_total
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = (time.perf_counter() - started) * 1000
    _request_count += 1
    _latency_ms_total += elapsed
    if response.status_code >= 500:
        _error_count += 1
    response.headers["x-request-id"] = request_id
    response.headers["x-process-time-ms"] = f"{elapsed:.2f}"
    response.headers["cache-control"] = "no-store"
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "member-risk-api"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if MODEL_SOURCE == "local" and not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model artifact is unavailable.")
    get_model()
    return {"status": "ready", "model_alias": MODEL_ALIAS}


@app.get("/model-info")
def model_info() -> dict[str, str | list[str] | None]:
    get_model()
    artifact = MODEL_PATH.name if MODEL_SOURCE == "local" else MODEL_URI
    return {
        "model_alias": MODEL_ALIAS,
        "model_source": MODEL_SOURCE,
        "artifact": artifact,
        "loaded_at": _model_loaded_at,
        "numeric_features": CHURN_NUMERIC,
        "categorical_features": CHURN_CATEGORICAL,
    }


@app.get("/metrics")
def metrics() -> Response:
    average = _latency_ms_total / max(_request_count, 1)
    body = (
        "# TYPE model_api_requests_total counter\n"
        f"model_api_requests_total {_request_count}\n"
        "# TYPE model_api_errors_total counter\n"
        f"model_api_errors_total {_error_count}\n"
        "# TYPE model_api_average_latency_ms gauge\n"
        f"model_api_average_latency_ms {average:.3f}\n"
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")


@app.post("/score/member-churn", response_model=ScoreResponse)
def score_member(payload: MemberFeatures, request: Request) -> ScoreResponse:
    model = get_model()
    row = pd.DataFrame([payload.model_dump()])
    probability = min(max(_predict_probability(model, row), 0.0), 1.0)
    band: Literal["LOW", "MEDIUM", "HIGH"]
    band = "HIGH" if probability >= 0.65 else "MEDIUM" if probability >= 0.35 else "LOW"
    return ScoreResponse(
        churn_probability=round(probability, 6),
        risk_band=band,
        model_alias=MODEL_ALIAS,
        scored_at=datetime.now(timezone.utc).isoformat(),
        request_id=request.state.request_id,
    )
