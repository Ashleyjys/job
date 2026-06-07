from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

RiskLevel = Literal["low", "medium", "high", "unknown"]
SourceStatusValue = Literal["ok", "degraded", "failed"]
MetricStatus = Literal["normal", "warning", "danger", "unknown"]
AnomalySeverity = Literal["none", "low", "medium", "high"]


class LocationInput(BaseModel):
    latitude: float
    longitude: float
    timezone: str | None = None


class DashboardQueryOptions(BaseModel):
    forecastDays: int | None = Field(default=None, ge=1, le=7)
    aqForecastDays: int | None = Field(default=None, ge=1, le=5)
    enableAnomalyDetection: bool | None = None


class DashboardRiskRules(BaseModel):
    highRiskThreshold: int | None = None
    mediumRiskThreshold: int | None = None
    aqiWeight: float | None = None
    pm25Weight: float | None = None
    pm10Weight: float | None = None
    weatherWeight: float | None = None


class DashboardQueryRequest(BaseModel):
    city: str | None = None
    location: LocationInput | None = None
    workflowId: str = "main"
    options: DashboardQueryOptions | None = None
    riskRules: DashboardRiskRules | None = None

    @model_validator(mode="after")
    def validate_city_or_location(self) -> "DashboardQueryRequest":
        if not self.city and not self.location:
            raise ValueError("Either city or location must be provided.")
        return self


class LocationInfo(BaseModel):
    name: str
    country: str | None = None
    admin1: str | None = None
    latitude: float
    longitude: float
    timezone: str


class MetricCardItem(BaseModel):
    key: str
    label: str
    value: int | float | str | None
    unit: str | None = None
    status: MetricStatus | None = None


class TrendPoint(BaseModel):
    time: str
    value: float | int | None


class TrendSeries(BaseModel):
    name: str
    data: list[TrendPoint]
    unit: str | None = None


class DailyWeatherForecast(BaseModel):
    date: str
    maxTemperature: float | None
    minTemperature: float | None
    maxWindSpeed: float | None


class CurrentWeather(BaseModel):
    observedAt: str
    temperature: float | None
    humidity: float | None
    windSpeed: float | None
    weatherCode: int | None


class WeatherTrendPoint(BaseModel):
    time: str
    temperature: float | None
    humidity: float | None
    windSpeed: float | None


class NormalizedWeather(BaseModel):
    source: Literal["open-meteo-weather"]
    status: SourceStatusValue
    location: LocationInfo
    current: CurrentWeather
    hourly: list[WeatherTrendPoint]
    daily: list[DailyWeatherForecast]


class CurrentAirQuality(BaseModel):
    observedAt: str
    aqi: int | None
    pm25: float | None
    pm10: float | None
    no2: float | None
    ozone: float | None


class AirQualityTrendPoint(BaseModel):
    time: str
    aqi: int | None
    pm25: float | None
    pm10: float | None
    no2: float | None
    ozone: float | None


class NormalizedAirQuality(BaseModel):
    source: Literal["open-meteo-air-quality"]
    status: SourceStatusValue
    location: LocationInfo
    current: CurrentAirQuality
    hourly: list[AirQualityTrendPoint]


class RiskScoreResult(BaseModel):
    riskScore: int | None
    riskLevel: RiskLevel
    primaryFactors: list[str]
    summary: str
    status: SourceStatusValue


class AnomalyResult(BaseModel):
    hasAnomaly: bool
    anomalyFlags: list[str]
    severity: AnomalySeverity
    messages: list[str]
    status: SourceStatusValue


class DataSourceStatus(BaseModel):
    weather: SourceStatusValue
    airQuality: SourceStatusValue
    analysis: SourceStatusValue


class DashboardViewModel(BaseModel):
    traceId: str
    workflowRunId: str
    location: LocationInfo
    currentMetrics: list[MetricCardItem]
    weatherTrend: list[TrendSeries]
    airQualityTrend: list[TrendSeries]
    dailyForecast: list[DailyWeatherForecast]
    risk: RiskScoreResult
    anomaly: AnomalyResult
    sourceStatus: DataSourceStatus
    notices: list[str]
    generatedAt: str
