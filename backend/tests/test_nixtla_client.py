import httpx

from app.services.nixtla_client import NixtlaClient, NixtlaConfig, NixtlaDisabledError


def test_nixtla_client_skips_remote_call_when_api_key_missing():
    client = NixtlaClient(config=NixtlaConfig(api_key=None, base_url="https://api.nixtla.io", timeout_ms=3000))

    try:
        client.detect_online_anomaly(
            hourly_points=[
                {"time": "2026-06-07T14:00:00Z", "aqi": 80, "pm25": 52.0},
                {"time": "2026-06-07T15:00:00Z", "aqi": 105, "pm25": 83.2},
            ]
        )
    except NixtlaDisabledError as exc:
        assert "api key" in str(exc).lower()
    else:
        raise AssertionError("Expected NixtlaDisabledError when API key is missing")


def test_nixtla_client_maps_remote_response_to_simple_result():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.url == httpx.URL("https://api.nixtla.io/v2/online_anomaly_detection")
        return httpx.Response(
            200,
            json={
                "anomaly": [False, True],
                "anomaly_score": [0.11, 0.93],
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NixtlaClient(
        http_client=http_client,
        config=NixtlaConfig(api_key="test-key", base_url="https://api.nixtla.io", timeout_ms=3000),
    )

    result = client.detect_online_anomaly(
        hourly_points=[
            {"time": "2026-06-07T14:00:00Z", "aqi": 80, "pm25": 52.0},
            {"time": "2026-06-07T15:00:00Z", "aqi": 105, "pm25": 83.2},
        ]
    )

    assert result.has_anomaly is True
    assert result.latest_flag is True
    assert result.score == 0.93
