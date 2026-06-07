from app.schemas.analysis import (
    AnalysisAirQualityInput,
    AnalysisAnomalyRequest,
    AnalysisHourlyAirQualityPoint,
    AnalysisRiskRequest,
    AnalysisRulesInput,
    AnalysisWeatherInput,
)
from app.services.analysis_service import detect_anomaly, score_risk
from app.services.nixtla_client import NixtlaAnomalyDetectionResult


def test_score_risk_returns_high_level_for_heavy_pollution():
    request = AnalysisRiskRequest(
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

    result = score_risk(request)

    assert result.riskLevel == "high"
    assert result.riskScore is not None
    assert result.riskScore >= 70
    assert "aqi" in result.primaryFactors


def test_detect_anomaly_returns_spike_when_aqi_rises_fast():
    request = AnalysisAnomalyRequest(
        enableDetection=True,
        hourlyAirQuality=[
            AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80),
            AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105),
        ],
    )

    result = detect_anomaly(request)

    assert result.hasAnomaly is True
    assert result.severity == "medium"
    assert result.anomalyFlags == ["aqi_spike"]


def test_detect_anomaly_returns_none_when_detection_disabled():
    request = AnalysisAnomalyRequest(
        enableDetection=False,
        hourlyAirQuality=[
            AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80),
            AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105),
        ],
    )

    result = detect_anomaly(request)

    assert result.hasAnomaly is False
    assert result.severity == "none"
    assert result.messages == []


class StubNixtlaClient:
    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error

    def detect_online_anomaly(self, hourly_points):
        if self._error:
            raise self._error
        return self._result


def test_detect_anomaly_uses_nixtla_result_when_available(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service._build_nixtla_client",
        lambda: StubNixtlaClient(result=NixtlaAnomalyDetectionResult(has_anomaly=True, latest_flag=True, score=0.91)),
    )

    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80, pm25=52.0),
                AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105, pm25=83.2),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.status == "ok"
    assert result.anomalyFlags == ["nixtla_online_anomaly"]


def test_detect_anomaly_falls_back_to_local_rules_when_nixtla_fails(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service._build_nixtla_client",
        lambda: StubNixtlaClient(error=RuntimeError("upstream unavailable")),
    )

    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.status == "degraded"
    assert result.anomalyFlags == ["aqi_spike"]


def test_detect_anomaly_with_local_rules_never_calls_nixtla(monkeypatch):
    class FailingNixtlaClient:
        def detect_online_anomaly(self, hourly_points):
            raise AssertionError("Nixtla should not be called for pure local fallback")

    monkeypatch.setattr(
        "app.services.analysis_service._build_nixtla_client",
        lambda: FailingNixtlaClient(),
    )

    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105),
            ],
        ),
        use_remote_detection=False,
    )

    assert result.hasAnomaly is True
    assert result.status == "ok"
    assert result.anomalyFlags == ["aqi_spike"]


def test_score_risk_uses_default_rules_when_rules_omitted():
    request = AnalysisRiskRequest(
        weather=AnalysisWeatherInput(
            temperature=30.0,
            humidity=45.0,
            windSpeed=2.5,
            weatherCode=1,
        ),
        airQuality=AnalysisAirQualityInput(
            aqi=90,
            pm25=40.0,
            pm10=60.0,
            no2=20.0,
            ozone=50.0,
        ),
    )

    result = score_risk(request)

    assert result.riskScore is not None
    assert result.riskLevel == "medium"
    assert result.status == "ok"


def test_score_risk_applies_pm10_weight_when_configured():
    request = AnalysisRiskRequest(
        weather=AnalysisWeatherInput(
            temperature=20.0,
            humidity=45.0,
            windSpeed=2.5,
            weatherCode=1,
        ),
        airQuality=AnalysisAirQualityInput(
            aqi=0,
            pm25=0.0,
            pm10=100.0,
            no2=20.0,
            ozone=50.0,
        ),
        rules=AnalysisRulesInput(
            highRiskThreshold=70,
            mediumRiskThreshold=40,
            aqiWeight=0.0,
            pm25Weight=0.0,
            weatherWeight=0.0,
            pm10Weight=0.5,
        ),
    )

    result = score_risk(request)

    assert result.riskScore == 50
    assert result.riskLevel == "medium"
    assert result.primaryFactors == ["pm10"]

