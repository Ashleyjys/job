import httpx

from app.schemas.analysis import (
    AnalysisAirQualityInput,
    AnalysisAnomalyRequest,
    AnalysisHourlyAirQualityPoint,
    AnalysisRiskRequest,
    AnalysisRulesInput,
    AnalysisWeatherInput,
)
from app.services.algorithm_service_client import AlgorithmServiceClient


def test_algorithm_service_client_calls_remote_score_risk_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("http://localhost:8100/score-risk")
        return httpx.Response(
            200,
            json={
                "riskScore": 76,
                "riskLevel": "high",
                "primaryFactors": ["aqi", "pm25"],
                "summary": "remote summary",
                "status": "ok",
            },
        )

    client = AlgorithmServiceClient(
        base_url="http://localhost:8100",
        timeout_ms=2000,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.score_risk(
        AnalysisRiskRequest(
            weather=AnalysisWeatherInput(
                temperature=36.0,
                humidity=52.0,
                windSpeed=3.2,
                weatherCode=1,
            ),
            airQuality=AnalysisAirQualityInput(
                aqi=126,
                pm25=83.1,
                pm10=118.0,
                no2=35.2,
                ozone=90.4,
            ),
            rules=AnalysisRulesInput(
                highRiskThreshold=70,
                mediumRiskThreshold=40,
            ),
        )
    )

    assert result.riskLevel == "high"
    assert result.summary == "remote summary"


def test_algorithm_service_client_calls_remote_detect_anomaly_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://localhost:8100/detect-anomaly")
        return httpx.Response(
            200,
            json={
                "hasAnomaly": True,
                "anomalyFlags": ["aqi_spike"],
                "severity": "medium",
                "messages": ["remote anomaly"],
                "status": "ok",
            },
        )

    client = AlgorithmServiceClient(
        base_url="http://localhost:8100",
        timeout_ms=2000,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-08T10:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-08T11:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.messages == ["remote anomaly"]
