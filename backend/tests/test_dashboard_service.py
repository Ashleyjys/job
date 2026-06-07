import httpx
import pytest

from app.schemas.dashboard import (
    AirQualityTrendPoint,
    AnomalyResult,
    CurrentAirQuality,
    CurrentWeather,
    DailyWeatherForecast,
    DashboardQueryOptions,
    DashboardQueryRequest,
    LocationInfo,
    NormalizedAirQuality,
    NormalizedWeather,
    RiskScoreResult,
    WeatherTrendPoint,
)
from app.services.dashboard_service import DashboardService
from app.services.workflow_loader import load_workflow


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


def test_dashboard_service_builds_view_model_from_upstream_data(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: StubAlgorithmServiceClient(),
    )
    service = DashboardService(upstream_client=StubUpstreamClient())
    request = DashboardQueryRequest(
        city="Beijing",
        options=DashboardQueryOptions(forecastDays=2, aqForecastDays=2, enableAnomalyDetection=True),
    )

    result = service.query_dashboard(request)

    assert result.location.name == "Beijing"
    assert result.sourceStatus.weather == "ok"
    assert result.sourceStatus.airQuality == "ok"
    assert result.sourceStatus.analysis == "ok"
    assert len(result.dailyForecast) == 2
    assert result.currentMetrics[0].key == "temperature"
    assert any(series.name == "AQI" for series in result.airQualityTrend)
    assert result.risk.riskScore is not None
    assert "aqi" in result.risk.primaryFactors


class FailingUpstreamClient:
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
        raise httpx.ConnectError(
            "upstream weather failed",
            request=httpx.Request("GET", "https://api.open-meteo.com/v1/forecast"),
        )


def test_dashboard_service_falls_back_to_mock_when_upstream_fails():
    service = DashboardService(upstream_client=FailingUpstreamClient())
    request = DashboardQueryRequest(city="Beijing")

    result = service.query_dashboard(request)

    assert result.location.name == "Beijing"
    assert result.notices
    assert result.sourceStatus.weather == "degraded"
    assert result.sourceStatus.airQuality == "degraded"
    assert result.sourceStatus.analysis == "degraded"


def test_dashboard_service_does_not_swallow_unexpected_internal_error(monkeypatch: pytest.MonkeyPatch):
    service = DashboardService(upstream_client=StubUpstreamClient())

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr(DashboardService, "_build_dashboard_view_model", staticmethod(raise_internal_error))

    with pytest.raises(RuntimeError, match="unexpected bug"):
        service.query_dashboard(DashboardQueryRequest(city="Beijing"))


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


def test_dashboard_service_uses_remote_algorithm_service_when_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: StubAlgorithmServiceClient(),
    )
    service = DashboardService(upstream_client=StubUpstreamClient())

    result = service.query_dashboard(DashboardQueryRequest(city="Beijing"))

    assert result.risk.summary == "remote risk"
    assert result.anomaly.messages == ["remote anomaly"]
    assert result.sourceStatus.analysis == "ok"


def test_dashboard_service_marks_analysis_degraded_when_local_anomaly_fallback_is_used(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: type(
            "FailingAlgorithmServiceClient",
            (),
            {
                "score_risk": lambda self, payload: (_ for _ in ()).throw(RuntimeError("algorithm service unavailable")),
                "detect_anomaly": lambda self, payload: (_ for _ in ()).throw(RuntimeError("algorithm service unavailable")),
            },
        )(),
    )

    service = DashboardService(upstream_client=StubUpstreamClient())
    result = service.query_dashboard(DashboardQueryRequest(city="Beijing"))

    assert result.risk.riskScore is not None
    assert result.anomaly.status == "degraded"
    assert result.sourceStatus.analysis == "degraded"


def test_dashboard_service_uses_runtime_risk_rule_weights_for_remote_algorithm_payload(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class CapturingAlgorithmServiceClient:
        def score_risk(self, payload):
            captured["score_payload"] = payload
            return RiskScoreResult(
                riskScore=62,
                riskLevel="medium",
                primaryFactors=["aqi"],
                summary="captured remote risk",
                status="ok",
            )

        def detect_anomaly(self, payload):
            return AnomalyResult(
                hasAnomaly=False,
                anomalyFlags=[],
                severity="none",
                messages=[],
                status="ok",
            )

    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        lambda timeout_ms=None: CapturingAlgorithmServiceClient(),
    )

    service = DashboardService(upstream_client=StubUpstreamClient())
    result = service.query_dashboard(
        DashboardQueryRequest(
            city="Beijing",
            riskRules={
                "highRiskThreshold": 88,
                "mediumRiskThreshold": 48,
                "aqiWeight": 0.2,
                "pm25Weight": 0.25,
                "pm10Weight": 0.15,
                "weatherWeight": 0.55,
            },
        )
    )

    rules = captured["score_payload"].rules
    assert rules is not None
    assert rules.highRiskThreshold == 88
    assert rules.mediumRiskThreshold == 48
    assert rules.aqiWeight == 0.2
    assert rules.pm25Weight == 0.25
    assert rules.pm10Weight == 0.15
    assert rules.weatherWeight == 0.55
    assert result.risk.summary == "captured remote risk"


def test_dashboard_service_uses_workflow_analysis_timeout_for_remote_algorithm_client(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_build_algorithm_service_client(timeout_ms):
        captured["timeout_ms"] = timeout_ms

        class StubAlgorithmServiceClient:
            def score_risk(self, payload):
                return RiskScoreResult(
                    riskScore=62,
                    riskLevel="medium",
                    primaryFactors=["aqi"],
                    summary="timeout-aware remote risk",
                    status="ok",
                )

            def detect_anomaly(self, payload):
                return AnomalyResult(
                    hasAnomaly=False,
                    anomalyFlags=[],
                    severity="none",
                    messages=[],
                    status="ok",
                )

        return StubAlgorithmServiceClient()

    monkeypatch.setattr(
        "app.services.dashboard_service._build_algorithm_service_client",
        fake_build_algorithm_service_client,
    )

    service = DashboardService(upstream_client=StubUpstreamClient())
    result = service.query_dashboard(
        DashboardQueryRequest(
            city="Beijing",
            options={
                "forecastDays": 2,
                "aqForecastDays": 2,
            },
        )
    )

    assert captured["timeout_ms"] == load_workflow("main").config.analysisTimeoutMs
    assert result.risk.summary == "timeout-aware remote risk"
