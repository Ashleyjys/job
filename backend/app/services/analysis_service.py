from __future__ import annotations

import httpx

from app.config import settings
from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisRiskRequest, AnalysisRulesInput
from app.schemas.dashboard import AnomalyResult, RiskScoreResult
from app.services.nixtla_client import (
    NixtlaClient,
    NixtlaConfig,
    NixtlaDisabledError,
)


def score_risk(request: AnalysisRiskRequest) -> RiskScoreResult:
    rules = request.rules or AnalysisRulesInput()
    aqi = request.airQuality.aqi or 0
    pm25 = request.airQuality.pm25 or 0.0
    pm10 = request.airQuality.pm10 or 0.0
    weather_penalty = rules.weatherWeight * 40 if (request.weather.temperature or 0) >= 35 else 0
    risk_score = min(
        100,
        round(aqi * rules.aqiWeight + pm25 * rules.pm25Weight + pm10 * rules.pm10Weight + weather_penalty),
    )

    if risk_score >= rules.highRiskThreshold:
        risk_level = "high"
    elif risk_score >= rules.mediumRiskThreshold:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskScoreResult(
        riskScore=risk_score,
        riskLevel=risk_level,
        primaryFactors=_build_primary_factors(aqi=aqi, pm25=pm25, pm10=pm10, rules=rules),
        summary="AQI 与 PM2.5 偏高，建议减少长时间户外活动并关注后续变化。",
        status="ok",
    )


def _build_primary_factors(*, aqi: int, pm25: float, pm10: float, rules: AnalysisRulesInput) -> list[str]:
    factors: list[str] = []
    if aqi > 0 and rules.aqiWeight > 0:
        factors.append("aqi")
    if pm25 >= 35 and rules.pm25Weight > 0:
        factors.append("pm25")
    if pm10 > 0 and rules.pm10Weight > 0:
        factors.append("pm10")
    return factors or ["aqi"]


def _build_nixtla_client() -> NixtlaClient:
    return NixtlaClient(
        config=NixtlaConfig(
            api_key=settings.nixtla_api_key,
            base_url=settings.nixtla_api_base_url,
            timeout_ms=settings.nixtla_timeout_ms,
        )
    )


def _detect_anomaly_with_local_rules(request: AnalysisAnomalyRequest, *, degraded: bool = False) -> AnomalyResult:
    hourly = request.hourlyAirQuality
    if len(hourly) < 2 or hourly[-1].aqi is None or hourly[0].aqi is None:
        return AnomalyResult(
            hasAnomaly=False,
            anomalyFlags=[],
            severity="none",
            messages=[],
            status="degraded" if degraded else "ok",
        )

    delta = hourly[-1].aqi - hourly[0].aqi
    has_anomaly = delta >= 20
    return AnomalyResult(
        hasAnomaly=has_anomaly,
        anomalyFlags=["aqi_spike"] if has_anomaly else [],
        severity="medium" if has_anomaly else "none",
        messages=["最近监测窗口内 AQI 上升较快。"] if has_anomaly else [],
        status="degraded" if degraded else "ok",
    )


def detect_anomaly(
    request: AnalysisAnomalyRequest,
    *,
    use_remote_detection: bool = True,
) -> AnomalyResult:
    if not request.enableDetection:
        return AnomalyResult(
            hasAnomaly=False,
            anomalyFlags=[],
            severity="none",
            messages=[],
            status="ok",
        )

    hourly = request.hourlyAirQuality
    if len(hourly) < 2:
        return _detect_anomaly_with_local_rules(request)

    if not use_remote_detection:
        return _detect_anomaly_with_local_rules(request)

    try:
        nixtla_result = _build_nixtla_client().detect_online_anomaly(
            hourly_points=[
                {
                    "time": point.time,
                    "aqi": point.aqi,
                    "pm25": point.pm25,
                }
                for point in hourly
            ]
        )
        return AnomalyResult(
            hasAnomaly=nixtla_result.has_anomaly,
            anomalyFlags=["nixtla_online_anomaly"] if nixtla_result.latest_flag else [],
            severity="medium" if nixtla_result.latest_flag else "none",
            messages=["Nixtla 检测到最新监测窗口存在异常波动。"] if nixtla_result.latest_flag else [],
            status="ok",
        )
    except NixtlaDisabledError:
        return _detect_anomaly_with_local_rules(request)
    except (RuntimeError, httpx.HTTPError, ValueError):
        return _detect_anomaly_with_local_rules(request, degraded=True)
