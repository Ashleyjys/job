# FastAPI Algorithm Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在同一仓库内新增一个可独立启动的 FastAPI 模拟算法服务，并让现有 `backend` 通过 HTTP 调用它，在算法服务不可用时回退到本地规则。

**Architecture:** 保留当前 `backend` 作为看板编排服务，在仓库中新增 `algorithm_service` 独立目录，提供 `/score-risk` 与 `/detect-anomaly` 两个 HTTP 接口。`backend` 新增一个轻量算法服务客户端，优先调用远端算法服务，失败时回退到本地规则，确保前端展示契约基本不变。

**Tech Stack:** FastAPI, Pydantic, httpx, pytest, Vue 3, TypeScript, Vite

---

### Task 1: Scaffold the standalone algorithm service with tests first

**Files:**
- Create: `D:\codex\job\algorithm_service\app\main.py`
- Create: `D:\codex\job\algorithm_service\app\routers\analysis.py`
- Create: `D:\codex\job\algorithm_service\app\schemas\analysis.py`
- Create: `D:\codex\job\algorithm_service\app\services\analysis_engine.py`
- Create: `D:\codex\job\algorithm_service\app\__init__.py`
- Create: `D:\codex\job\algorithm_service\app\routers\__init__.py`
- Create: `D:\codex\job\algorithm_service\app\services\__init__.py`
- Create: `D:\codex\job\algorithm_service\app\schemas\__init__.py`
- Create: `D:\codex\job\algorithm_service\tests\test_analysis_engine.py`
- Create: `D:\codex\job\algorithm_service\tests\test_analysis_router.py`
- Create: `D:\codex\job\algorithm_service\requirements.txt`

- [ ] **Step 1: Write the failing algorithm service tests**

```python
# D:\codex\job\algorithm_service\tests\test_analysis_engine.py
from app.schemas.analysis import (
    AnalysisAirQualityInput,
    AnalysisAnomalyRequest,
    AnalysisHourlyAirQualityPoint,
    AnalysisRiskRequest,
    AnalysisRulesInput,
    AnalysisWeatherInput,
)
from app.services.analysis_engine import detect_anomaly, score_risk


def test_score_risk_returns_high_level_for_heavy_pollution():
    result = score_risk(
        AnalysisRiskRequest(
            weather=AnalysisWeatherInput(temperature=36.0, humidity=52.0, windSpeed=3.2, weatherCode=1),
            airQuality=AnalysisAirQualityInput(aqi=126, pm25=83.1, pm10=118.0, no2=35.2, ozone=90.4),
            rules=AnalysisRulesInput(highRiskThreshold=70, mediumRiskThreshold=40),
        )
    )

    assert result.riskLevel == "high"
    assert result.riskScore is not None


def test_detect_anomaly_returns_spike_when_aqi_rises_fast():
    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-08T10:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-08T11:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.anomalyFlags == ["aqi_spike"]
```

```python
# D:\codex\job\algorithm_service\tests\test_analysis_router.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_score_risk_endpoint_returns_analysis_result():
    response = client.post(
        "/score-risk",
        json={
            "weather": {"temperature": 36.0, "humidity": 52.0, "windSpeed": 3.2, "weatherCode": 1},
            "airQuality": {"aqi": 126, "pm25": 83.1, "pm10": 118.0, "no2": 35.2, "ozone": 90.4},
            "rules": {"highRiskThreshold": 70, "mediumRiskThreshold": 40},
        },
    )

    assert response.status_code == 200
    assert response.json()["riskLevel"] in {"low", "medium", "high"}


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `..\.condaenv\python.exe -m pytest tests -v`
Workdir: `D:\codex\job\algorithm_service`
Expected: FAIL because the service files do not exist yet

- [ ] **Step 3: Implement the minimal standalone FastAPI service**

```python
# D:\codex\job\algorithm_service\app\main.py
from fastapi import FastAPI

from app.routers.analysis import router as analysis_router

app = FastAPI(title="Mock Analysis Service")
app.include_router(analysis_router)
```

```python
# D:\codex\job\algorithm_service\app\routers\analysis.py
from fastapi import APIRouter

from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisRiskRequest
from app.schemas.analysis import AnomalyResult, RiskScoreResult
from app.services.analysis_engine import detect_anomaly, score_risk

router = APIRouter()


@router.post("/score-risk", response_model=RiskScoreResult)
def score_risk_endpoint(payload: AnalysisRiskRequest) -> RiskScoreResult:
    return score_risk(payload)


@router.post("/detect-anomaly", response_model=AnomalyResult)
def detect_anomaly_endpoint(payload: AnalysisAnomalyRequest) -> AnomalyResult:
    return detect_anomaly(payload)
```

```python
# D:\codex\job\algorithm_service\app\services\analysis_engine.py
from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisRiskRequest, AnalysisRulesInput
from app.schemas.analysis import AnomalyResult, RiskScoreResult


def score_risk(request: AnalysisRiskRequest) -> RiskScoreResult:
    rules = request.rules or AnalysisRulesInput()
    aqi = request.airQuality.aqi or 0
    pm25 = request.airQuality.pm25 or 0.0
    weather_penalty = rules.weatherWeight * 40 if (request.weather.temperature or 0) >= 35 else 0
    risk_score = min(100, round(aqi * rules.aqiWeight + pm25 * rules.pm25Weight + weather_penalty))

    if risk_score >= rules.highRiskThreshold:
        risk_level = "high"
    elif risk_score >= rules.mediumRiskThreshold:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskScoreResult(
        riskScore=risk_score,
        riskLevel=risk_level,
        primaryFactors=["aqi", "pm25"] if pm25 >= 35 else ["aqi"],
        summary="AQI 与 PM2.5 偏高，建议减少长时间户外活动并关注后续变化。",
        status="ok",
    )


def detect_anomaly(request: AnalysisAnomalyRequest) -> AnomalyResult:
    if not request.enableDetection:
        return AnomalyResult(hasAnomaly=False, anomalyFlags=[], severity="none", messages=[], status="ok")

    hourly = request.hourlyAirQuality
    if len(hourly) < 2 or hourly[-1].aqi is None or hourly[0].aqi is None:
        return AnomalyResult(hasAnomaly=False, anomalyFlags=[], severity="none", messages=[], status="ok")

    delta = hourly[-1].aqi - hourly[0].aqi
    has_anomaly = delta >= 20
    return AnomalyResult(
        hasAnomaly=has_anomaly,
        anomalyFlags=["aqi_spike"] if has_anomaly else [],
        severity="medium" if has_anomaly else "none",
        messages=["最近监测窗口内 AQI 上升较快。"] if has_anomaly else [],
        status="ok",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `..\.condaenv\python.exe -m pytest tests -v`
Workdir: `D:\codex\job\algorithm_service`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add algorithm_service
git commit -m "feat: add standalone fastapi algorithm service"
```

### Task 2: Add backend HTTP client for the algorithm service

**Files:**
- Modify: `D:\codex\job\backend\app\config.py`
- Create: `D:\codex\job\backend\app\services\algorithm_service_client.py`
- Create: `D:\codex\job\backend\tests\test_algorithm_service_client.py`
- Modify: `D:\codex\job\.env.example`

- [ ] **Step 1: Write the failing backend client tests**

```python
# D:\codex\job\backend\tests\test_algorithm_service_client.py
import httpx

from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisHourlyAirQualityPoint, AnalysisRiskRequest, AnalysisAirQualityInput, AnalysisRulesInput, AnalysisWeatherInput
from app.services.algorithm_service_client import AlgorithmServiceClient


def test_algorithm_service_client_calls_remote_score_risk_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("http://localhost:8100/score-risk")
        return httpx.Response(200, json={
            "riskScore": 76,
            "riskLevel": "high",
            "primaryFactors": ["aqi", "pm25"],
            "summary": "remote summary",
            "status": "ok",
        })

    client = AlgorithmServiceClient(
        base_url="http://localhost:8100",
        timeout_ms=2000,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.score_risk(
        AnalysisRiskRequest(
            weather=AnalysisWeatherInput(temperature=36.0, humidity=52.0, windSpeed=3.2, weatherCode=1),
            airQuality=AnalysisAirQualityInput(aqi=126, pm25=83.1, pm10=118.0, no2=35.2, ozone=90.4),
            rules=AnalysisRulesInput(highRiskThreshold=70, mediumRiskThreshold=40),
        )
    )

    assert result.riskLevel == "high"
    assert result.summary == "remote summary"


def test_algorithm_service_client_calls_remote_detect_anomaly_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://localhost:8100/detect-anomaly")
        return httpx.Response(200, json={
            "hasAnomaly": True,
            "anomalyFlags": ["aqi_spike"],
            "severity": "medium",
            "messages": ["remote anomaly"],
            "status": "ok",
        })

    client = AlgorithmServiceClient(
        base_url="http://localhost:8100",
        timeout_ms=2000,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-08T10:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-08T11:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.messages == ["remote anomaly"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `..\.condaenv\python.exe -m pytest tests/test_algorithm_service_client.py -v`
Workdir: `D:\codex\job\backend`
Expected: FAIL because `algorithm_service_client.py` does not exist yet

- [ ] **Step 3: Implement the backend client and config**

```python
# D:\codex\job\backend\app\config.py
class Settings(BaseSettings):
    # existing fields...
    algorithm_service_base_url: str = "http://localhost:8100"
    algorithm_service_timeout_ms: int = 2000
```

```python
# D:\codex\job\backend\app\services\algorithm_service_client.py
from __future__ import annotations

import httpx

from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisRiskRequest
from app.schemas.dashboard import AnomalyResult, RiskScoreResult


class AlgorithmServiceClient:
    def __init__(self, base_url: str, timeout_ms: int, http_client: httpx.Client | None = None) -> None:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `..\.condaenv\python.exe -m pytest tests/test_algorithm_service_client.py -v`
Workdir: `D:\codex\job\backend`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/services/algorithm_service_client.py backend/tests/test_algorithm_service_client.py .env.example
git commit -m "feat: add backend client for algorithm service"
```

### Task 3: Route dashboard analysis through the remote algorithm service with fallback

**Files:**
- Modify: `D:\codex\job\backend\app\services\dashboard_service.py`
- Modify: `D:\codex\job\backend\app\services\analysis_service.py`
- Modify: `D:\codex\job\backend\tests\test_dashboard_service.py`

- [ ] **Step 1: Write the failing dashboard integration tests**

```python
# D:\codex\job\backend\tests\test_dashboard_service.py
from app.schemas.dashboard import AnomalyResult, RiskScoreResult


class StubAlgorithmServiceClient:
    def score_risk(self, payload):
        return RiskScoreResult(
            riskScore=77,
            riskLevel="high",
            primaryFactors=["aqi", "pm25"],
            summary="remote risk",
            status="ok",
        )

    def detect_anomaly(self, payload):
        return AnomalyResult(
            hasAnomaly=True,
            anomalyFlags=["aqi_spike"],
            severity="medium",
            messages=["remote anomaly"],
            status="ok",
        )


def test_dashboard_service_uses_remote_algorithm_service_when_available(monkeypatch):
    monkeypatch.setattr("app.services.dashboard_service._build_algorithm_service_client", lambda: StubAlgorithmServiceClient())
    service = DashboardService(upstream_client=StubUpstreamClient())

    result = service.query_dashboard(DashboardQueryRequest(city="Beijing"))

    assert result.risk.summary == "remote risk"
    assert result.anomaly.messages == ["remote anomaly"]
    assert result.sourceStatus.analysis == "ok"


def test_dashboard_service_falls_back_to_local_analysis_when_algorithm_service_fails(monkeypatch):
    class FailingAlgorithmServiceClient:
        def score_risk(self, payload):
            raise RuntimeError("algorithm service unavailable")

        def detect_anomaly(self, payload):
            raise RuntimeError("algorithm service unavailable")

    monkeypatch.setattr("app.services.dashboard_service._build_algorithm_service_client", lambda: FailingAlgorithmServiceClient())
    service = DashboardService(upstream_client=StubUpstreamClient())

    result = service.query_dashboard(DashboardQueryRequest(city="Beijing"))

    assert result.risk.riskScore is not None
    assert result.anomaly.status == "degraded"
    assert result.sourceStatus.analysis == "degraded"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `..\.condaenv\python.exe -m pytest tests/test_dashboard_service.py -v`
Workdir: `D:\codex\job\backend`
Expected: FAIL because dashboard still uses local analysis directly

- [ ] **Step 3: Implement remote-first analysis with fallback**

```python
# D:\codex\job\backend\app\services\dashboard_service.py
from app.services.algorithm_service_client import AlgorithmServiceClient


def _build_algorithm_service_client() -> AlgorithmServiceClient:
    return AlgorithmServiceClient(
        base_url=settings.algorithm_service_base_url,
        timeout_ms=settings.algorithm_service_timeout_ms,
    )
```

```python
# in _build_dashboard_view_model(...)
try:
    algorithm_client = _build_algorithm_service_client()
    risk = algorithm_client.score_risk(risk_request)
    anomaly = algorithm_client.detect_anomaly(anomaly_request)
except (RuntimeError, httpx.HTTPError, ValueError):
    risk = score_risk(risk_request)
    anomaly = detect_anomaly(anomaly_request)
    risk = risk.model_copy(update={"status": "degraded"})
    anomaly = anomaly.model_copy(update={"status": "degraded"})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `..\.condaenv\python.exe -m pytest tests/test_dashboard_service.py -v`
Workdir: `D:\codex\job\backend`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/dashboard_service.py backend/app/services/analysis_service.py backend/tests/test_dashboard_service.py
git commit -m "feat: use remote algorithm service with fallback"
```

### Task 4: Update docs and run full verification

**Files:**
- Modify: `D:\codex\job\README.md`
- Modify: `D:\codex\job\docs\02-architecture.md`
- Modify: `D:\codex\job\docs\03-api-spec.md`
- Modify: `D:\codex\job\.env.example`

- [ ] **Step 1: Update docs to describe the two-service setup**

```markdown
- `backend` is the orchestration service
- `algorithm_service` is the standalone FastAPI mock algorithm service
- `backend` calls `algorithm_service` over HTTP and falls back locally when unavailable
```

- [ ] **Step 2: Add algorithm service runtime config to the env example**

```env
ALGORITHM_SERVICE_BASE_URL=http://localhost:8100
ALGORITHM_SERVICE_TIMEOUT_MS=2000
```

- [ ] **Step 3: Run full verification for both services and frontend**

Run: `..\.condaenv\python.exe -m pytest tests -v`
Workdir: `D:\codex\job\algorithm_service`
Expected: PASS

Run: `..\.condaenv\python.exe -m pytest tests -v`
Workdir: `D:\codex\job\backend`
Expected: PASS

Run: `npm run test -- --run`
Workdir: `D:\codex\job\frontend`
Expected: PASS

- [ ] **Step 4: Run a quick dual-service smoke check**

Run algorithm service: `..\.condaenv\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100`
Workdir: `D:\codex\job\algorithm_service`

Run backend: `..\.condaenv\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
Workdir: `D:\codex\job\backend`

Then call backend:
`curl.exe -X POST http://127.0.0.1:8000/api/v1/dashboard/query -H "Content-Type: application/json" -d "{\"city\":\"Beijing\"}"`
Expected: `200` and a dashboard payload with risk/anomaly fields populated

- [ ] **Step 5: Commit**

```bash
git add README.md docs/02-architecture.md docs/03-api-spec.md .env.example
git commit -m "docs: describe standalone fastapi algorithm service"
```
