from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import (
    AirQualityTrendPoint,
    AnomalyResult,
    CurrentAirQuality,
    CurrentWeather,
    DailyWeatherForecast,
    LocationInfo,
    NormalizedAirQuality,
    NormalizedWeather,
    RiskScoreResult,
    WeatherTrendPoint,
)
from app.services.dashboard_service import DashboardService

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


class StubUpstreamClient:
    def search_city(self, city: str) -> LocationInfo:
        return LocationInfo(
            name=city,
            country="China",
            admin1="Beijing",
            latitude=39.9042,
            longitude=116.4074,
            timezone="Asia/Shanghai",
        )

    def fetch_weather(self, location: LocationInfo, forecast_days: int, timeout_ms: int) -> NormalizedWeather:
        return NormalizedWeather(
            source="open-meteo-weather",
            status="ok",
            location=location,
            current=CurrentWeather(
                observedAt="2026-06-07T14:00:00Z",
                temperature=31.5,
                humidity=52,
                windSpeed=3.2,
                weatherCode=1,
            ),
            hourly=[
                WeatherTrendPoint(time="2026-06-07T14:00:00Z", temperature=31.5, humidity=52, windSpeed=3.2),
                WeatherTrendPoint(time="2026-06-07T15:00:00Z", temperature=32.2, humidity=50, windSpeed=3.6),
            ],
            daily=[
                DailyWeatherForecast(date="2026-06-07", maxTemperature=34.0, minTemperature=24.0, maxWindSpeed=5.0),
                DailyWeatherForecast(date="2026-06-08", maxTemperature=35.0, minTemperature=25.0, maxWindSpeed=5.4),
                DailyWeatherForecast(date="2026-06-09", maxTemperature=36.0, minTemperature=26.0, maxWindSpeed=5.7),
            ],
        )

    def fetch_air_quality(self, location: LocationInfo, forecast_days: int, timeout_ms: int) -> NormalizedAirQuality:
        return NormalizedAirQuality(
            source="open-meteo-air-quality",
            status="ok",
            location=location,
            current=CurrentAirQuality(
                observedAt="2026-06-07T14:00:00Z",
                aqi=126,
                pm25=83.1,
                pm10=118.0,
                no2=35.2,
                ozone=90.4,
            ),
            hourly=[
                AirQualityTrendPoint(time="2026-06-07T14:00:00Z", aqi=126, pm25=83.1, pm10=118.0, no2=35.2, ozone=90.4),
                AirQualityTrendPoint(time="2026-06-07T15:00:00Z", aqi=132, pm25=88.0, pm10=122.0, no2=36.1, ozone=92.0),
            ],
        )


def test_dashboard_query_returns_view_model_for_city(monkeypatch):
    monkeypatch.setattr(
        "app.routers.dashboard.dashboard_service",
        DashboardService(upstream_client=StubUpstreamClient()),
    )
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
    monkeypatch.setattr(
        "app.routers.dashboard.dashboard_service",
        DashboardService(upstream_client=StubUpstreamClient()),
    )
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
