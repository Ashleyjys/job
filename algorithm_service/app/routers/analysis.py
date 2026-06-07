from fastapi import APIRouter

from app.schemas.analysis import (
    AnalysisAnomalyRequest,
    AnalysisRiskRequest,
    AnomalyResult,
    RiskScoreResult,
)
from app.services.analysis_engine import detect_anomaly, score_risk

router = APIRouter()


@router.post("/score-risk", response_model=RiskScoreResult)
def score_risk_endpoint(payload: AnalysisRiskRequest) -> RiskScoreResult:
    return score_risk(payload)


@router.post("/detect-anomaly", response_model=AnomalyResult)
def detect_anomaly_endpoint(payload: AnalysisAnomalyRequest) -> AnomalyResult:
    return detect_anomaly(payload)
