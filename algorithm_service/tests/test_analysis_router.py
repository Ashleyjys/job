from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_score_risk_endpoint_returns_analysis_result():
    response = client.post(
        "/score-risk",
        json={
            "weather": {
                "temperature": 36.0,
                "humidity": 52.0,
                "windSpeed": 3.2,
                "weatherCode": 1,
            },
            "airQuality": {
                "aqi": 126,
                "pm2_5": 83.1,
                "pm10": 118.0,
                "no2": 35.2,
                "ozone": 90.4,
            },
            "rules": {
                "highRiskThreshold": 70,
                "mediumRiskThreshold": 40,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["riskLevel"] == "high"
    assert body["primaryFactors"] == ["aqi", "pm25"]


def test_detect_anomaly_endpoint_returns_analysis_result():
    response = client.post(
        "/detect-anomaly",
        json={
            "enableDetection": True,
            "hourlyAirQuality": [
                {"time": "2026-06-08T10:00:00Z", "aqi": 80},
                {"time": "2026-06-08T11:00:00Z", "aqi": 105},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["hasAnomaly"] is True
