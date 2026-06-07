from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class WorkflowThresholds(BaseModel):
    mediumRisk: int
    highRisk: int


class WorkflowTimeouts(BaseModel):
    weather: int
    airQuality: int


class WorkflowConfig(BaseModel):
    enableAnomalyDetection: bool
    forecastDays: int
    aqForecastDays: int
    upstreamTimeoutMs: WorkflowTimeouts
    analysisTimeoutMs: int
    thresholds: WorkflowThresholds


class WorkflowStep(BaseModel):
    id: str
    type: str
    onError: str | None = None
    dependsOn: list[str] = Field(default_factory=list)
    action: str | None = None
    when: str | None = None
    mode: str | None = None
    timeoutMs: int | None = None
    result: str | None = None
    retry: dict[str, Any] | None = None


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    version: int
    inputs: dict[str, Any]
    config: WorkflowConfig
    steps: list[WorkflowStep]


def _workflow_file_path(workflow_id: str) -> Path:
    return Path(__file__).resolve().parents[3] / "workflows" / f"{workflow_id}.yaml"


@lru_cache(maxsize=8)
def load_workflow(workflow_id: str) -> WorkflowDefinition:
    workflow_path = _workflow_file_path(workflow_id)
    raw_definition = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    return WorkflowDefinition.model_validate(raw_definition)
