from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import AnomalyResult, RiskScoreResult

client = TestClient(app)


class StubAlgorithmServiceClient:
    def score_risk(self, payload):
        return RiskScoreResult(
            riskScore=77,
            riskLevel="high",
            primaryFactors=["aqi", "pm25"],
            summary="remote risk",
            status="ok",
        )

    def detect_anomaly(self, payload):
        return AnomalyResult(
            hasAnomaly=True,
            anomalyFlags=["aqi_spike"],
            severity="medium",
            messages=["remote anomaly"],
            status="ok",
        )


def test_dashboard_query_returns_view_model_for_city(monkeypatch):
    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: type(
            "RouterStubAlgorithmServiceClient",
            (),
            {
                "score_risk": lambda self, payload: StubAlgorithmServiceClient().score_risk(payload),
                "detect_anomaly": lambda self, payload: StubAlgorithmServiceClient().detect_anomaly(payload),
            },
        )(),
    )

    response = client.post("/api/v1/dashboard/query", json={"city": "Beijing"})

    assert response.status_code == 200
    body = response.json()
    assert body["location"]["name"] == "Beijing"
    assert body["workflowRunId"]
    assert body["traceId"]
    assert body["sourceStatus"] == {
        "weather": "ok",
        "airQuality": "ok",
        "analysis": "ok",
    }
    assert len(body["currentMetrics"]) >= 4
    assert len(body["weatherTrend"]) >= 1
    assert len(body["airQualityTrend"]) >= 1
    assert len(body["dailyForecast"]) >= 1
    assert body["risk"]["riskLevel"] in {"low", "medium", "high"}


def test_dashboard_query_requires_city_or_location():
    response = client.post("/api/v1/dashboard/query", json={})

    assert response.status_code == 422


def test_dashboard_query_applies_runtime_workflow_options(monkeypatch):
    stub = StubAlgorithmServiceClient()
    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: type(
            "RouterStubAlgorithmServiceClient",
            (),
            {
                "score_risk": lambda self, payload: stub.score_risk(payload),
                "detect_anomaly": lambda self, payload: AnomalyResult(
                    hasAnomaly=False,
                    anomalyFlags=[],
                    severity="none",
                    messages=[],
                    status="ok",
                ),
            },
        )(),
    )

    response = client.post(
        "/api/v1/dashboard/query",
        json={
            "city": "Beijing",
            "options": {
                "forecastDays": 3,
                "enableAnomalyDetection": False,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["dailyForecast"]) == 3
    assert body["anomaly"]["hasAnomaly"] is False
    assert body["anomaly"]["severity"] == "none"


def test_dashboard_query_allows_cors_preflight_for_local_frontend():
    response = client.options(
        "/api/v1/dashboard/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]
