from __future__ import annotations

import uuid

from locust import HttpUser, between, task


PAYLOAD = {
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


class ScoringUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        with self.client.get("/ready", name="ready-startup", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"service not ready: {response.status_code}")

    @task(8)
    def score(self) -> None:
        headers = {"x-request-id": str(uuid.uuid4())}
        with self.client.post(
            "/score/member-churn",
            json=PAYLOAD,
            headers=headers,
            name="score-member-churn",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status: {response.status_code}")
                return
            body = response.json()
            if body.get("risk_band") not in {"LOW", "MEDIUM", "HIGH"}:
                response.failure("response contract missing valid risk_band")

    @task(1)
    def readiness(self) -> None:
        self.client.get("/ready", name="ready")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="health")
