from __future__ import annotations

from dataclasses import dataclass

import httpx


class NixtlaDisabledError(RuntimeError):
    pass


@dataclass(frozen=True)
class NixtlaConfig:
    api_key: str | None
    base_url: str
    timeout_ms: int


@dataclass(frozen=True)
class NixtlaAnomalyDetectionResult:
    has_anomaly: bool
    latest_flag: bool
    score: float | None


class NixtlaClient:
    def __init__(self, http_client: httpx.Client | None = None, *, config: NixtlaConfig) -> None:
        self._http_client = http_client or httpx.Client()
        self._config = config

    def detect_online_anomaly(self, hourly_points: list[dict[str, float | int | str | None]]) -> NixtlaAnomalyDetectionResult:
        if not self._config.api_key:
            raise NixtlaDisabledError("Nixtla API key is not configured.")

        if not hourly_points:
            raise ValueError("At least one hourly point is required.")

        payload = {
            "series": {
                "y": [point.get("aqi") for point in hourly_points],
                "sizes": [len(hourly_points)],
            },
            "freq": "H",
            "detection_size": 1,
            "h": 1,
        }
        response = self._http_client.post(
            f"{self._config.base_url.rstrip('/')}/v2/online_anomaly_detection",
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self._config.timeout_ms / 1000,
        )
        response.raise_for_status()
        body = response.json()
        anomalies = body.get("anomaly") or []
        scores = body.get("anomaly_score") or body.get("scores") or []
        latest_flag = bool(anomalies[-1]) if anomalies else False
        score = float(scores[-1]) if scores else None

        return NixtlaAnomalyDetectionResult(
            has_anomaly=any(bool(item) for item in anomalies),
            latest_flag=latest_flag,
            score=score,
        )
