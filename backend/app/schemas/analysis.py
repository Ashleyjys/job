from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.dashboard import AnomalyResult, RiskScoreResult


class AnalysisWeatherInput(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    windSpeed: float | None = None
    weatherCode: int | None = None


class AnalysisAirQualityInput(BaseModel):
    aqi: int | None = None
    pm25: float | None = Field(default=None, alias="pm2_5")
    pm10: float | None = None
    no2: float | None = None
    ozone: float | None = None

    model_config = {"populate_by_name": True}


class AnalysisRulesInput(BaseModel):
    highRiskThreshold: int = 70
    mediumRiskThreshold: int = 40
    aqiWeight: float = 0.45
    pm25Weight: float = 0.35
    pm10Weight: float = 0.0
    weatherWeight: float = 0.20


class AnalysisRiskRequest(BaseModel):
    weather: AnalysisWeatherInput
    airQuality: AnalysisAirQualityInput
    rules: AnalysisRulesInput | None = None


class AnalysisHourlyAirQualityPoint(BaseModel):
    time: str
    aqi: int | None = None
    pm25: float | None = None
    pm10: float | None = None
    no2: float | None = None
    ozone: float | None = None


class AnalysisAnomalyRequest(BaseModel):
    enableDetection: bool = True
    hourlyAirQuality: list[AnalysisHourlyAirQualityPoint]


__all__ = [
    "AnalysisAirQualityInput",
    "AnalysisAnomalyRequest",
    "AnalysisHourlyAirQualityPoint",
    "AnalysisRiskRequest",
    "AnalysisRulesInput",
    "AnalysisWeatherInput",
    "AnomalyResult",
    "RiskScoreResult",
]
