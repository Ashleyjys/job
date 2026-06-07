from app.schemas.analysis import (
    AnalysisAirQualityInput,
    AnalysisAnomalyRequest,
    AnalysisHourlyAirQualityPoint,
    AnalysisRiskRequest,
    AnalysisRulesInput,
    AnalysisWeatherInput,
)
from app.services.analysis_engine import detect_anomaly, score_risk


def test_score_risk_returns_high_level_for_heavy_pollution():
    result = score_risk(
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
    assert result.riskScore is not None


def test_detect_anomaly_returns_spike_when_aqi_rises_fast():
    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-08T10:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-08T11:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.anomalyFlags == ["aqi_spike"]


def test_score_risk_applies_pm10_weight_when_configured():
    result = score_risk(
        AnalysisRiskRequest(
            weather=AnalysisWeatherInput(
                temperature=20.0,
                humidity=52.0,
                windSpeed=3.2,
                weatherCode=1,
            ),
            airQuality=AnalysisAirQualityInput(
                aqi=0,
                pm25=0.0,
                pm10=100.0,
                no2=35.2,
                ozone=90.4,
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
    )

    assert result.riskScore == 50
    assert result.riskLevel == "medium"
    assert result.primaryFactors == ["pm10"]
