from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx

from app.config import settings
from app.schemas.analysis import (
    AnalysisAirQualityInput,
    AnalysisAnomalyRequest,
    AnalysisHourlyAirQualityPoint,
    AnalysisRiskRequest,
    AnalysisRulesInput,
    AnalysisWeatherInput,
)
from app.schemas.dashboard import (
    DashboardQueryRequest,
    DashboardViewModel,
    DataSourceStatus,
    LocationInfo,
    MetricCardItem,
    TrendPoint,
    TrendSeries,
)
from app.services.analysis_service import detect_anomaly, score_risk
from app.services.algorithm_service_client import AlgorithmServiceClient
from app.services.mock_dashboard_data import build_mock_dashboard_view_model
from app.services.open_meteo_client import OpenMeteoClient
from app.services.workflow_loader import WorkflowDefinition, load_workflow


class DashboardService:
    def __init__(self, upstream_client: OpenMeteoClient | None = None) -> None:
        self._upstream_client = upstream_client or OpenMeteoClient(
            geocoding_base_url=settings.geocoding_api_base_url,
            weather_base_url=settings.weather_api_base_url,
            air_quality_base_url=settings.air_quality_api_base_url,
        )

    def query_dashboard(self, request: DashboardQueryRequest) -> DashboardViewModel:
        workflow = self._build_runtime_workflow(request)
        analysis_rules = _build_analysis_rules(request, workflow)
        try:
            location = self._resolve_location(request)
        except (httpx.HTTPError, ValueError) as exc:
            if settings.enable_mock_fallback:
                return self._build_fallback_dashboard(request=request, workflow=workflow, fallback_notice=_fallback_notice_from_exception(exc))
            raise

        try:
            weather = self._upstream_client.fetch_weather(
                location=location,
                forecast_days=workflow.config.forecastDays,
                timeout_ms=workflow.config.upstreamTimeoutMs.weather,
            )
            air_quality = self._upstream_client.fetch_air_quality(
                location=location,
                forecast_days=workflow.config.aqForecastDays,
                timeout_ms=workflow.config.upstreamTimeoutMs.airQuality,
            )
        except httpx.HTTPError as exc:
            if settings.enable_mock_fallback:
                return self._build_fallback_dashboard(request=request, workflow=workflow, fallback_notice=_fallback_notice_from_exception(exc))
            raise

        return self._build_dashboard_view_model(
            workflow=workflow,
            location=location,
            weather=weather,
            air_quality=air_quality,
            analysis_rules=analysis_rules,
        )

    def _resolve_location(self, request: DashboardQueryRequest) -> LocationInfo:
        if request.location:
            return LocationInfo(
                name=request.city or "Custom Location",
                country="China",
                admin1=None,
                latitude=request.location.latitude,
                longitude=request.location.longitude,
                timezone=request.location.timezone or "Asia/Shanghai",
            )
        if not request.city:
            raise ValueError("City is required when location is not provided.")
        return self._upstream_client.search_city(request.city)

    @staticmethod
    def _resolve_location_from_request_or_default(request: DashboardQueryRequest) -> LocationInfo:
        if request.location:
            return LocationInfo(
                name=request.city or "Custom Location",
                country="China",
                admin1=None,
                latitude=request.location.latitude,
                longitude=request.location.longitude,
                timezone=request.location.timezone or "Asia/Shanghai",
            )
        return LocationInfo(
            name=request.city or "Beijing",
            country="China",
            admin1="Beijing",
            latitude=39.9042,
            longitude=116.4074,
            timezone="Asia/Shanghai",
        )

    @staticmethod
    def _build_fallback_dashboard(
        request: DashboardQueryRequest,
        workflow: WorkflowDefinition,
        fallback_notice: str,
    ) -> DashboardViewModel:
        location = DashboardService._resolve_location_from_request_or_default(request)
        return build_mock_dashboard_view_model(
            location=location,
            workflow=workflow,
            fallback_notice=fallback_notice,
        )

    @staticmethod
    def _build_runtime_workflow(request: DashboardQueryRequest) -> WorkflowDefinition:
        workflow = load_workflow(request.workflowId)
        runtime_workflow = workflow.model_copy(deep=True)

        if request.options:
            if request.options.forecastDays is not None:
                runtime_workflow.config.forecastDays = request.options.forecastDays
            if request.options.aqForecastDays is not None:
                runtime_workflow.config.aqForecastDays = request.options.aqForecastDays
            if request.options.enableAnomalyDetection is not None:
                runtime_workflow.config.enableAnomalyDetection = request.options.enableAnomalyDetection

        if request.riskRules:
            if request.riskRules.mediumRiskThreshold is not None:
                runtime_workflow.config.thresholds.mediumRisk = request.riskRules.mediumRiskThreshold
            if request.riskRules.highRiskThreshold is not None:
                runtime_workflow.config.thresholds.highRisk = request.riskRules.highRiskThreshold

        return runtime_workflow

    @staticmethod
    def _build_dashboard_view_model(
        workflow: WorkflowDefinition,
        location: LocationInfo,
        weather,
        air_quality,
        analysis_rules: AnalysisRulesInput,
    ) -> DashboardViewModel:
        now = datetime.now(tz=UTC).replace(microsecond=0)
        risk_request = AnalysisRiskRequest(
            weather=AnalysisWeatherInput(
                temperature=weather.current.temperature,
                humidity=weather.current.humidity,
                windSpeed=weather.current.windSpeed,
                weatherCode=weather.current.weatherCode,
            ),
            airQuality=AnalysisAirQualityInput(
                aqi=air_quality.current.aqi,
                pm25=air_quality.current.pm25,
                pm10=air_quality.current.pm10,
                no2=air_quality.current.no2,
                ozone=air_quality.current.ozone,
            ),
            rules=analysis_rules,
        )
        anomaly_request = AnalysisAnomalyRequest(
            enableDetection=workflow.config.enableAnomalyDetection,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(
                    time=item.time,
                    aqi=item.aqi,
                    pm25=item.pm25,
                    pm10=item.pm10,
                    no2=item.no2,
                    ozone=item.ozone,
                )
                for item in air_quality.hourly
            ],
        )

        try:
            algorithm_client = _build_algorithm_service_client(workflow.config.analysisTimeoutMs)
            risk = algorithm_client.score_risk(risk_request)
            anomaly = algorithm_client.detect_anomaly(anomaly_request)
        except (RuntimeError, httpx.HTTPError, ValueError):
            risk = score_risk(risk_request).model_copy(update={"status": "degraded"})
            anomaly = detect_anomaly(
                anomaly_request,
                use_remote_detection=False,
            ).model_copy(update={"status": "degraded"})

        current_metrics = [
            MetricCardItem(key="temperature", label="Temperature", value=weather.current.temperature, unit="C", status="normal"),
            MetricCardItem(key="humidity", label="Humidity", value=weather.current.humidity, unit="%", status="normal"),
            MetricCardItem(key="aqi", label="AQI", value=air_quality.current.aqi, unit="AQI", status=_risk_status_from_aqi(air_quality.current.aqi)),
            MetricCardItem(key="pm25", label="PM2.5", value=air_quality.current.pm25, unit="ug/m3", status=_risk_status_from_aqi(air_quality.current.aqi)),
        ]
        analysis_status = "ok" if risk.status == "ok" and anomaly.status == "ok" else "degraded"

        return DashboardViewModel(
            traceId=uuid4().hex,
            workflowRunId=f"{workflow.id}-{uuid4().hex[:8]}",
            location=location,
            currentMetrics=current_metrics,
            weatherTrend=[
                TrendSeries(
                    name="Temperature",
                    unit="C",
                    data=[TrendPoint(time=item.time, value=item.temperature) for item in weather.hourly],
                ),
                TrendSeries(
                    name="Humidity",
                    unit="%",
                    data=[TrendPoint(time=item.time, value=item.humidity) for item in weather.hourly],
                ),
            ],
            airQualityTrend=[
                TrendSeries(
                    name="AQI",
                    unit="AQI",
                    data=[TrendPoint(time=item.time, value=item.aqi) for item in air_quality.hourly],
                ),
                TrendSeries(
                    name="PM2.5",
                    unit="ug/m3",
                    data=[TrendPoint(time=item.time, value=item.pm25) for item in air_quality.hourly],
                ),
            ],
            dailyForecast=weather.daily,
            risk=risk,
            anomaly=anomaly,
            sourceStatus=DataSourceStatus(weather=weather.status, airQuality=air_quality.status, analysis=analysis_status),
            notices=[],
            generatedAt=now.isoformat().replace("+00:00", "Z"),
        )


dashboard_service = DashboardService()


def _build_algorithm_service_client(timeout_ms: int | None = None) -> AlgorithmServiceClient:
    return AlgorithmServiceClient(
        base_url=settings.algorithm_service_base_url,
        timeout_ms=timeout_ms or settings.algorithm_service_timeout_ms,
    )


def _build_analysis_rules(
    request: DashboardQueryRequest,
    workflow: WorkflowDefinition,
) -> AnalysisRulesInput:
    default_rules = AnalysisRulesInput()
    risk_rules = request.riskRules
    return AnalysisRulesInput(
        highRiskThreshold=workflow.config.thresholds.highRisk,
        mediumRiskThreshold=workflow.config.thresholds.mediumRisk,
        aqiWeight=risk_rules.aqiWeight if risk_rules and risk_rules.aqiWeight is not None else default_rules.aqiWeight,
        pm25Weight=risk_rules.pm25Weight if risk_rules and risk_rules.pm25Weight is not None else default_rules.pm25Weight,
        pm10Weight=risk_rules.pm10Weight if risk_rules and risk_rules.pm10Weight is not None else default_rules.pm10Weight,
        weatherWeight=risk_rules.weatherWeight if risk_rules and risk_rules.weatherWeight is not None else default_rules.weatherWeight,
    )


def _risk_status_from_aqi(aqi: int | None) -> str:
    if aqi is None:
        return "unknown"
    if aqi >= 150:
        return "danger"
    if aqi >= 80:
        return "warning"
    return "normal"


def _fallback_notice_from_exception(exc: Exception) -> str:
    if isinstance(exc, ValueError):
        return "城市解析失败，当前展示本地 mock 数据。"
    return "上游天气或空气质量数据暂不可用，当前展示本地 mock 数据。"
