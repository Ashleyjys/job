from __future__ import annotations

import unicodedata
from typing import Any

import httpx

from app.schemas.dashboard import (
    AirQualityTrendPoint,
    CurrentAirQuality,
    CurrentWeather,
    DailyWeatherForecast,
    LocationInfo,
    NormalizedAirQuality,
    NormalizedWeather,
    WeatherTrendPoint,
)

KNOWN_CHINESE_CITY_ALIASES = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "天津": "Tianjin",
    "重庆": "Chongqing",
    "广州": "Guangzhou",
    "深圳": "Shenzhen",
    "成都": "Chengdu",
    "杭州": "Hangzhou",
    "南京": "Nanjing",
    "苏州": "Suzhou",
    "武汉": "Wuhan",
    "西安": "Xi'an",
    "长沙": "Changsha",
    "郑州": "Zhengzhou",
    "青岛": "Qingdao",
    "宁波": "Ningbo",
    "厦门": "Xiamen",
    "福州": "Fuzhou",
    "济南": "Jinan",
    "沈阳": "Shenyang",
    "大连": "Dalian",
    "哈尔滨": "Harbin",
    "长春": "Changchun",
    "石家庄": "Shijiazhuang",
    "太原": "Taiyuan",
    "合肥": "Hefei",
    "南昌": "Nanchang",
    "昆明": "Kunming",
    "南宁": "Nanning",
    "贵阳": "Guiyang",
    "海口": "Haikou",
    "三亚": "Sanya",
    "兰州": "Lanzhou",
    "西宁": "Xining",
    "银川": "Yinchuan",
    "呼和浩特": "Hohhot",
    "乌鲁木齐": "Urumqi",
    "拉萨": "Lhasa",
    "香港": "Hong Kong",
    "澳门": "Macau",
}


class OpenMeteoClient:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        *,
        geocoding_base_url: str,
        weather_base_url: str,
        air_quality_base_url: str,
    ) -> None:
        self._http_client = http_client or httpx.Client()
        self._geocoding_base_url = geocoding_base_url.rstrip("/")
        self._weather_base_url = weather_base_url.rstrip("/")
        self._air_quality_base_url = air_quality_base_url.rstrip("/")

    def search_cities(self, city: str, count: int = 8) -> list[LocationInfo]:
        for language in _preferred_geocoding_languages(city):
            locations = self._search_cities_by_language(city=city, count=count, language=language)
            if locations:
                return _finalize_locations(query=city, locations=locations, count=count)

        alias = _resolve_known_chinese_city_alias(city)
        if alias:
            locations = self._search_cities_by_language(city=alias, count=count, language="en")
            if locations:
                return _finalize_locations(query=alias, locations=locations, count=count)

        return []

    def _search_cities_by_language(self, city: str, count: int, language: str) -> list[LocationInfo]:
        response = self._http_client.get(
            f"{self._geocoding_base_url}/v1/search",
            params={
                "name": city,
                "count": count,
                "language": language,
                "format": "json",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        selected_results = _select_city_level_results(results)
        return [self._normalize_location(item) for item in selected_results]

    def search_city(self, city: str) -> LocationInfo:
        results = self.search_cities(city, count=8)
        if not results:
            raise ValueError(f"City not found: {city}")
        return results[0]

    def fetch_weather(self, location: LocationInfo, forecast_days: int, timeout_ms: int) -> NormalizedWeather:
        response = self._http_client.get(
            f"{self._weather_base_url}/v1/forecast",
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": forecast_days,
            },
            timeout=timeout_ms / 1000,
        )
        response.raise_for_status()
        payload = response.json()

        current = payload["current"]
        hourly = payload["hourly"]
        daily = payload["daily"]

        return NormalizedWeather(
            source="open-meteo-weather",
            status="ok",
            location=location.model_copy(update={"timezone": payload.get("timezone", location.timezone)}),
            current=CurrentWeather(
                observedAt=current["time"],
                temperature=current.get("temperature_2m"),
                humidity=current.get("relative_humidity_2m"),
                windSpeed=current.get("wind_speed_10m"),
                weatherCode=current.get("weather_code"),
            ),
            hourly=self._normalize_weather_hourly(hourly),
            daily=self._normalize_weather_daily(daily),
        )

    def fetch_air_quality(self, location: LocationInfo, forecast_days: int, timeout_ms: int) -> NormalizedAirQuality:
        response = self._http_client.get(
            f"{self._air_quality_base_url}/v1/air-quality",
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone",
                "hourly": "us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone",
                "timezone": "auto",
                "forecast_days": forecast_days,
                "domains": "auto",
            },
            timeout=timeout_ms / 1000,
        )
        response.raise_for_status()
        payload = response.json()

        current = payload["current"]
        hourly = payload["hourly"]

        return NormalizedAirQuality(
            source="open-meteo-air-quality",
            status="ok",
            location=location.model_copy(update={"timezone": payload.get("timezone", location.timezone)}),
            current=CurrentAirQuality(
                observedAt=current["time"],
                aqi=current.get("us_aqi"),
                pm25=current.get("pm2_5"),
                pm10=current.get("pm10"),
                no2=current.get("nitrogen_dioxide"),
                ozone=current.get("ozone"),
            ),
            hourly=self._normalize_air_quality_hourly(hourly),
        )

    @staticmethod
    def _normalize_location(raw: dict[str, Any]) -> LocationInfo:
        return LocationInfo(
            name=raw["name"],
            country=raw.get("country"),
            admin1=raw.get("admin1"),
            latitude=raw["latitude"],
            longitude=raw["longitude"],
            timezone=raw["timezone"],
        )

    @staticmethod
    def _normalize_weather_hourly(hourly: dict[str, list[Any]]) -> list[WeatherTrendPoint]:
        records = []
        for index, time in enumerate(hourly.get("time", [])):
            records.append(
                WeatherTrendPoint(
                    time=time,
                    temperature=_value_at(hourly.get("temperature_2m"), index),
                    humidity=_value_at(hourly.get("relative_humidity_2m"), index),
                    windSpeed=_value_at(hourly.get("wind_speed_10m"), index),
                )
            )
        return records

    @staticmethod
    def _normalize_weather_daily(daily: dict[str, list[Any]]) -> list[DailyWeatherForecast]:
        records = []
        for index, date in enumerate(daily.get("time", [])):
            records.append(
                DailyWeatherForecast(
                    date=date,
                    maxTemperature=_value_at(daily.get("temperature_2m_max"), index),
                    minTemperature=_value_at(daily.get("temperature_2m_min"), index),
                    maxWindSpeed=_value_at(daily.get("wind_speed_10m_max"), index),
                )
            )
        return records

    @staticmethod
    def _normalize_air_quality_hourly(hourly: dict[str, list[Any]]) -> list[AirQualityTrendPoint]:
        records = []
        for index, time in enumerate(hourly.get("time", [])):
            records.append(
                AirQualityTrendPoint(
                    time=time,
                    aqi=_value_at(hourly.get("us_aqi"), index),
                    pm25=_value_at(hourly.get("pm2_5"), index),
                    pm10=_value_at(hourly.get("pm10"), index),
                    no2=_value_at(hourly.get("nitrogen_dioxide"), index),
                    ozone=_value_at(hourly.get("ozone"), index),
                )
            )
        return records


def _value_at(values: list[Any] | None, index: int) -> Any:
    if not values or index >= len(values):
        return None
    return values[index]


def _finalize_locations(query: str, locations: list[LocationInfo], count: int) -> list[LocationInfo]:
    ranked_locations = _rerank_locations(query, locations)
    unique_locations = _deduplicate_locations(ranked_locations)
    return unique_locations[:count]


def _rerank_locations(query: str, locations: list[LocationInfo]) -> list[LocationInfo]:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return locations

    ranked_locations = sorted(
        enumerate(locations),
        key=lambda item: _location_sort_key(normalized_query, item[1], item[0]),
    )
    return [location for _, location in ranked_locations]


def _location_sort_key(query: str, location: LocationInfo, original_index: int) -> tuple[int, int, int, int, int, int, int]:
    normalized_name = _normalize_search_text(location.name)
    tokens = normalized_name.split()
    compact_name = normalized_name.replace(" ", "")
    compact_query = query.replace(" ", "")

    exact_name = 0 if normalized_name == query else 1
    prefix_match = 0 if normalized_name.startswith(query) else 1
    word_prefix_match = 0 if any(token.startswith(compact_query) for token in tokens) else 1
    substring_match = 0 if compact_query in compact_name else 1
    length_gap = abs(len(compact_name) - len(compact_query))

    return (
        exact_name,
        prefix_match,
        word_prefix_match,
        substring_match,
        length_gap,
        len(compact_name),
        original_index,
    )


def _normalize_search_text(value: str) -> str:
    normalized_value = unicodedata.normalize("NFKD", value)
    normalized_chars = []

    for char in normalized_value:
        if unicodedata.combining(char):
            continue
        normalized_chars.append(char.lower() if char.isalnum() else " ")

    return " ".join("".join(normalized_chars).split())


def _preferred_geocoding_languages(query: str) -> tuple[str, str]:
    if _contains_cjk(query):
        return ("zh", "en")

    return ("en", "zh")


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def _resolve_known_chinese_city_alias(query: str) -> str | None:
    if not _contains_cjk(query):
        return None

    return KNOWN_CHINESE_CITY_ALIASES.get(query.strip())


def _deduplicate_locations(locations: list[LocationInfo]) -> list[LocationInfo]:
    unique_locations: list[LocationInfo] = []
    seen_signatures: set[tuple[str, str, str]] = set()

    for location in locations:
        signature = (
            _normalize_search_text(location.name),
            _normalize_search_text(location.admin1 or ""),
            _normalize_search_text(location.country or ""),
        )
        if signature in seen_signatures:
            continue

        seen_signatures.add(signature)
        unique_locations.append(location)

    return unique_locations


def _select_city_level_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    city_level_results = [item for item in results if _is_city_level_result(item)]
    return city_level_results or results


def _is_city_level_result(raw: dict[str, Any]) -> bool:
    feature_code = raw.get("feature_code")
    if not isinstance(feature_code, str):
        return False

    return feature_code == "PPLC" or feature_code.startswith("PPLA")
