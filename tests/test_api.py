from fastapi.testclient import TestClient

from hospitality_data_platform.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_model_info():
    response = client.get("/model-info")
    assert response.status_code == 200
    assert response.json()["model_alias"] == "Champion"
    assert "avg_booking_lead_days_12m" in response.json()["numeric_features"]


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "model_api_requests_total" in response.text


def test_score():
    payload = {
        "tenure_months": 36,
        "points_earned_12m": 28000,
        "points_redeemed_12m": 8000,
        "points_expired_12m": 2500,
        "points_utilization_rate": 0.2857,
        "expired_share": 0.089,
        "stays_12m": 1,
        "room_nights_12m": 4,
        "net_room_revenue_12m": 1250,
        "avg_booking_lead_days_12m": 42,
        "service_cases_90d": 2,
        "escalated_cases_90d": 1,
        "avg_resolution_hours_90d": 52,
        "days_since_last_booking": 230,
        "member_tier": "Member",
        "home_market": "Orlando",
    }
    response = client.post("/score/member-churn", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["churn_probability"] <= 1
    assert body["risk_band"] in {"LOW", "MEDIUM", "HIGH"}
    assert body["model_alias"] == "Champion"
    assert body["request_id"] == response.headers["x-request-id"]


def test_invalid_payload_is_rejected():
    response = client.post(
        "/score/member-churn",
        json={
            "tenure_months": -1,
            "points_earned_12m": 0,
            "points_redeemed_12m": 0,
            "points_expired_12m": 0,
            "points_utilization_rate": 0,
            "expired_share": 0,
            "stays_12m": 0,
            "room_nights_12m": 0,
            "net_room_revenue_12m": 0,
            "avg_booking_lead_days_12m": 0,
            "service_cases_90d": 0,
            "escalated_cases_90d": 0,
            "avg_resolution_hours_90d": 0,
            "days_since_last_booking": 0,
            "member_tier": "Member",
            "home_market": "Orlando",
        },
    )
    assert response.status_code == 422
