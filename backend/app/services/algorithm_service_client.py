from __future__ import annotations

import httpx

from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisRiskRequest
from app.schemas.dashboard import AnomalyResult, RiskScoreResult


class AlgorithmServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout_ms: int,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_ms / 1000
        self._http_client = http_client or httpx.Client()

    def score_risk(self, payload: AnalysisRiskRequest) -> RiskScoreResult:
        response = self._http_client.post(
            f"{self._base_url}/score-risk",
            json=payload.model_dump(mode="json", by_alias=True),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return RiskScoreResult.model_validate(response.json())

    def detect_anomaly(self, payload: AnalysisAnomalyRequest) -> AnomalyResult:
        response = self._http_client.post(
            f"{self._base_url}/detect-anomaly",
            json=payload.model_dump(mode="json", by_alias=True),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return AnomalyResult.model_validate(response.json())
