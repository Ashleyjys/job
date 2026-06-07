from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.schemas.dashboard import (
    AnomalyResult,
    DailyWeatherForecast,
    DashboardViewModel,
    DataSourceStatus,
    LocationInfo,
    MetricCardItem,
    RiskScoreResult,
    TrendPoint,
    TrendSeries,
)
from app.services.workflow_loader import WorkflowDefinition


CITY_CATALOG: dict[str, LocationInfo] = {
    "beijing": LocationInfo(
        name="Beijing",
        country="China",
        admin1="Beijing",
        latitude=39.9042,
        longitude=116.4074,
        timezone="Asia/Shanghai",
    ),
    "shanghai": LocationInfo(
        name="Shanghai",
        country="China",
        admin1="Shanghai",
        latitude=31.2304,
        longitude=121.4737,
        timezone="Asia/Shanghai",
    ),
    "guangzhou": LocationInfo(
        name="Guangzhou",
        country="China",
        admin1="Guangdong",
        latitude=23.1291,
        longitude=113.2644,
        timezone="Asia/Shanghai",
    ),
    "shenzhen": LocationInfo(
        name="Shenzhen",
        country="China",
        admin1="Guangdong",
        latitude=22.5431,
        longitude=114.0579,
        timezone="Asia/Shanghai",
    ),
}


def resolve_city(city: str | None) -> LocationInfo:
    if city:
        return CITY_CATALOG.get(city.strip().lower(), CITY_CATALOG["beijing"])
    return CITY_CATALOG["beijing"]


def _build_weather_trend(base_time: datetime) -> list[TrendSeries]:
    temperature = []
    humidity = []
    for index in range(6):
        point_time = (base_time + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        temperature.append(TrendPoint(time=point_time, value=28 + index))
        humidity.append(TrendPoint(time=point_time, value=52 - index))
    return [
        TrendSeries(name="Temperature", unit="C", data=temperature),
        TrendSeries(name="Humidity", unit="%", data=humidity),
    ]


def _build_air_quality_trend(base_time: datetime) -> list[TrendSeries]:
    aqi = []
    pm25 = []
    for index in range(6):
        point_time = (base_time + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        aqi.append(TrendPoint(time=point_time, value=72 + index * 4))
        pm25.append(TrendPoint(time=point_time, value=42 + index * 3))
    return [
        TrendSeries(name="AQI", unit="AQI", data=aqi),
        TrendSeries(name="PM2.5", unit="ug/m3", data=pm25),
    ]


def _build_daily_forecast(base_time: datetime, days: int) -> list[DailyWeatherForecast]:
    forecast = []
    for index in range(days):
        forecast_date = (base_time + timedelta(days=index)).strftime("%Y-%m-%d")
        forecast.append(
            DailyWeatherForecast(
                date=forecast_date,
                maxTemperature=31 + index,
                minTemperature=22 + index,
                maxWindSpeed=4.2 + index * 0.3,
            )
        )
    return forecast


def _build_risk_result(workflow: WorkflowDefinition) -> RiskScoreResult:
    risk_score = 68
    if risk_score >= workflow.config.thresholds.highRisk:
        risk_level = "high"
    elif risk_score >= workflow.config.thresholds.mediumRisk:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskScoreResult(
        riskScore=risk_score,
        riskLevel=risk_level,
        primaryFactors=["aqi", "pm25"],
        summary="AQI 与 PM2.5 指标偏高，建议减少长时间户外活动。",
        status="degraded",
    )


def build_mock_dashboard_view_model(
    location: LocationInfo,
    workflow: WorkflowDefinition,
    fallback_notice: str | None = None,
) -> DashboardViewModel:
    now = datetime.now(tz=UTC).replace(microsecond=0)
    current_metrics = [
        MetricCardItem(key="temperature", label="Temperature", value=30.4, unit="C", status="normal"),
        MetricCardItem(key="humidity", label="Humidity", value=58, unit="%", status="normal"),
        MetricCardItem(key="aqi", label="AQI", value=78, unit="AQI", status="warning"),
        MetricCardItem(key="pm25", label="PM2.5", value=48.6, unit="ug/m3", status="warning"),
    ]
    anomaly = AnomalyResult(
        hasAnomaly=True,
        anomalyFlags=["aqi_spike"],
        severity="medium",
        messages=["最近 3 小时 AQI 上升较快，请关注短时空气质量波动。"],
        status="degraded",
    )
    notices = ["当前无法获取实时上游数据，已回退到本地 mock 数据。"]
    if fallback_notice:
        notices.insert(0, fallback_notice)

    return DashboardViewModel(
        traceId=uuid4().hex,
        workflowRunId=f"{workflow.id}-{uuid4().hex[:8]}",
        location=location,
        currentMetrics=current_metrics,
        weatherTrend=_build_weather_trend(now),
        airQualityTrend=_build_air_quality_trend(now),
        dailyForecast=_build_daily_forecast(now, workflow.config.forecastDays),
        risk=_build_risk_result(workflow),
        anomaly=anomaly if workflow.config.enableAnomalyDetection else anomaly.model_copy(
            update={"hasAnomaly": False, "anomalyFlags": [], "severity": "none", "messages": [], "status": "degraded"}
        ),
        sourceStatus=DataSourceStatus(weather="degraded", airQuality="degraded", analysis="degraded"),
        notices=notices,
        generatedAt=now.isoformat().replace("+00:00", "Z"),
    )
