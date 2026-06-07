import httpx

from app.services.open_meteo_client import OpenMeteoClient


def test_open_meteo_client_normalizes_geocoding_weather_and_air_quality():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Beijing",
                            "latitude": 39.9075,
                            "longitude": 116.39723,
                            "country": "China",
                            "admin1": "Beijing Municipality",
                            "timezone": "Asia/Shanghai",
                        }
                    ]
                },
            )

        if "air-quality-api.open-meteo.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "latitude": 39.9075,
                    "longitude": 116.39723,
                    "timezone": "Asia/Shanghai",
                    "current": {
                        "time": "2026-06-07T14:00",
                        "us_aqi": 118,
                        "pm2_5": 82.4,
                        "pm10": 120.2,
                        "nitrogen_dioxide": 36.1,
                        "ozone": 88.4,
                    },
                    "hourly": {
                        "time": ["2026-06-07T14:00", "2026-06-07T15:00"],
                        "us_aqi": [118, 123],
                        "pm2_5": [82.4, 86.0],
                        "pm10": [120.2, 126.4],
                        "nitrogen_dioxide": [36.1, 37.2],
                        "ozone": [88.4, 90.0],
                    },
                },
            )

        if "api.open-meteo.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "latitude": 39.9075,
                    "longitude": 116.39723,
                    "timezone": "Asia/Shanghai",
                    "current": {
                        "time": "2026-06-07T14:00",
                        "temperature_2m": 30.1,
                        "relative_humidity_2m": 61,
                        "wind_speed_10m": 3.8,
                        "weather_code": 1,
                    },
                    "hourly": {
                        "time": ["2026-06-07T14:00", "2026-06-07T15:00"],
                        "temperature_2m": [30.1, 31.2],
                        "relative_humidity_2m": [61, 58],
                        "wind_speed_10m": [3.8, 4.2],
                    },
                    "daily": {
                        "time": ["2026-06-07", "2026-06-08"],
                        "temperature_2m_max": [34.2, 35.0],
                        "temperature_2m_min": [24.6, 25.1],
                        "wind_speed_10m_max": [5.2, 5.8],
                    },
                },
            )

        raise AssertionError(f"Unexpected request URL: {request.url}")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    location = client.search_city("Beijing")
    weather = client.fetch_weather(location=location, forecast_days=2, timeout_ms=5000)
    air_quality = client.fetch_air_quality(location=location, forecast_days=2, timeout_ms=5000)

    assert location.name == "Beijing"
    assert location.country == "China"
    assert location.timezone == "Asia/Shanghai"

    assert weather.current.temperature == 30.1
    assert weather.current.humidity == 61
    assert weather.hourly[1].temperature == 31.2
    assert weather.daily[0].maxTemperature == 34.2

    assert air_quality.current.aqi == 118
    assert air_quality.current.pm25 == 82.4
    assert air_quality.hourly[1].aqi == 123


def test_open_meteo_client_returns_multiple_location_candidates():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        assert request.url.params["count"] == "3"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Chengdu",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Chengdu Shi",
                        "latitude": 31.0,
                        "longitude": 104.5,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Chengdu County",
                        "latitude": 30.1,
                        "longitude": 103.9,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("Chengdu", count=3)

    assert len(results) == 3
    assert results[0].name == "Chengdu"
    assert results[1].admin1 == "Sichuan"


def test_open_meteo_client_reranks_prefix_matches_ahead_of_fuzzy_candidates():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        assert request.url.params["count"] == "5"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Zhengzhou",
                        "latitude": 34.75778,
                        "longitude": 113.64861,
                        "country": "China",
                        "admin1": "Henan",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Chengdu",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Kawasan Perindustrian Cheng",
                        "latitude": 2.2618,
                        "longitude": 102.2317,
                        "country": "Malaysia",
                        "admin1": "Melaka",
                        "timezone": "Asia/Kuala_Lumpur",
                    },
                    {
                        "name": "Chengde",
                        "latitude": 40.9519,
                        "longitude": 117.95883,
                        "country": "China",
                        "admin1": "Hebei",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Lhasa",
                        "latitude": 29.63842,
                        "longitude": 91.04441,
                        "country": "China",
                        "admin1": "Tibet",
                        "timezone": "Asia/Shanghai",
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("cheng", count=5)

    assert [item.name for item in results[:3]] == ["Chengdu", "Chengde", "Kawasan Perindustrian Cheng"]


def test_open_meteo_client_search_city_uses_multiple_candidates_for_best_match():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        if request.url.params["count"] == "1":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Zhengzhou",
                            "latitude": 34.75778,
                            "longitude": 113.64861,
                            "country": "China",
                            "admin1": "Henan",
                            "timezone": "Asia/Shanghai",
                        }
                    ]
                },
            )

        assert request.url.params["count"] == "8"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Zhengzhou",
                        "latitude": 34.75778,
                        "longitude": 113.64861,
                        "country": "China",
                        "admin1": "Henan",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "Chengdu",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    result = client.search_city("Chengdu")

    assert result.name == "Chengdu"


def test_open_meteo_client_prefers_zh_search_for_chinese_queries():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        calls.append(request.url.params["language"])
        assert request.url.params["name"] == "\u5317\u4eac"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "\u5317\u4eac",
                        "latitude": 39.9075,
                        "longitude": 116.39723,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u5317\u4eac\u5e02",
                        "timezone": "Asia/Shanghai",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    result = client.search_city("\u5317\u4eac")

    assert result.name == "\u5317\u4eac"
    assert result.country == "\u4e2d\u56fd"
    assert calls == ["zh"]


def test_open_meteo_client_falls_back_to_secondary_language_when_primary_search_is_empty():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        language = request.url.params["language"]
        calls.append(language)
        if language == "zh":
            return httpx.Response(200, json={"results": []})

        assert language == "en"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Beijing",
                        "latitude": 39.9075,
                        "longitude": 116.39723,
                        "country": "China",
                        "admin1": "Beijing Municipality",
                        "timezone": "Asia/Shanghai",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("\u5317\u4eac", count=3)

    assert [item.name for item in results] == ["Beijing"]
    assert calls == ["zh", "en"]


def test_open_meteo_client_retries_known_chinese_city_with_english_alias_when_upstream_returns_empty():
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        name = request.url.params["name"]
        language = request.url.params["language"]
        calls.append((name, language))

        if name == "\u6210\u90fd":
            return httpx.Response(200, json={"results": []})

        assert name == "Chengdu"
        assert language == "en"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Chengdu",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "China",
                        "admin1": "Sichuan",
                        "timezone": "Asia/Shanghai",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("\u6210\u90fd", count=3)

    assert [item.name for item in results] == ["Chengdu"]
    assert calls == [("\u6210\u90fd", "zh"), ("\u6210\u90fd", "en"), ("Chengdu", "en")]


def test_open_meteo_client_deduplicates_identical_city_candidates_but_keeps_distinct_regions():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        assert request.url.params["language"] == "zh"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u56db\u5ddd",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u56db\u5ddd",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 26.36828,
                        "longitude": 115.34289,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u6c5f\u897f",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u56db\u5ddd",
                        "timezone": "Asia/Shanghai",
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("\u6210\u90fd", count=8)

    assert [(item.name, item.admin1, item.country) for item in results] == [
        ("\u6210\u90fd", "\u56db\u5ddd", "\u4e2d\u56fd"),
        ("\u6210\u90fd", "\u6c5f\u897f", "\u4e2d\u56fd"),
    ]


def test_open_meteo_client_filters_non_city_level_candidates_when_city_results_exist():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        assert request.url.params["language"] == "zh"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 30.66667,
                        "longitude": 104.06667,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u56db\u5ddd",
                        "admin2": "\u6210\u90fd\u5e02",
                        "feature_code": "PPLA",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 26.983,
                        "longitude": 114.207,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u6c5f\u897f",
                        "admin2": "\u5409\u5b89\u5e02",
                        "feature_code": "PPL",
                        "timezone": "Asia/Shanghai",
                    },
                    {
                        "name": "\u6210\u90fd",
                        "latitude": 31.11537,
                        "longitude": 107.44296,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u56db\u5ddd",
                        "admin2": "\u8fbe\u5dde\u5e02",
                        "feature_code": "PPL",
                        "timezone": "Asia/Shanghai",
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("\u6210\u90fd", count=8)

    assert [(item.name, item.admin1, item.country) for item in results] == [
        ("\u6210\u90fd", "\u56db\u5ddd", "\u4e2d\u56fd"),
    ]


def test_open_meteo_client_keeps_non_city_candidates_when_no_city_level_results_exist():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" not in str(request.url):
            raise AssertionError(f"Unexpected request URL: {request.url}")

        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "\u6c34\u53e3",
                        "latitude": 27.12972,
                        "longitude": 114.74806,
                        "country": "\u4e2d\u56fd",
                        "admin1": "\u6c5f\u897f",
                        "admin2": "\u5409\u5b89\u5e02",
                        "feature_code": "PPL",
                        "timezone": "Asia/Shanghai",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenMeteoClient(
        http_client=http_client,
        geocoding_base_url="https://geocoding-api.open-meteo.com",
        weather_base_url="https://api.open-meteo.com",
        air_quality_base_url="https://air-quality-api.open-meteo.com",
    )

    results = client.search_cities("\u6c34\u53e3", count=8)

    assert [(item.name, item.admin1, item.country) for item in results] == [
        ("\u6c34\u53e3", "\u6c5f\u897f", "\u4e2d\u56fd"),
    ]
