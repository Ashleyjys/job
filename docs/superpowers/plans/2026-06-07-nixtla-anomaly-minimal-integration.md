# Nixtla Anomaly Detection Minimal Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在尽量少改动现有项目的前提下，把异常检测升级为 Nixtla 优先、本地规则回退，并保持现有前端契约不变。

**Architecture:** 保留当前 Open-Meteo 数据链路和 `/api/v1/analysis/*` 内部接口边界，只在后端分析服务后面新增一个 Nixtla HTTP 适配层。异常检测先尝试第三方算法 API，失败或未配置 key 时回退到本地规则，并用现有 `AnomalyResult` 结构对外返回。

**Tech Stack:** FastAPI, Pydantic Settings, httpx, pytest, YAML workflow config, Vue frontend (no structural changes required)

---

### Task 1: Add configuration and client tests first

**Files:**
- Modify: `D:\codex\job\backend\app\config.py`
- Modify: `D:\codex\job\.env.example`
- Add: `D:\codex\job\backend\tests\test_nixtla_client.py`

- [ ] **Step 1: Write the failing client/config tests**

```python
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
                "scores": [0.11, 0.93],
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `..\.condaenv\python.exe -m pytest tests/test_nixtla_client.py -v`
Expected: FAIL with `ModuleNotFoundError` or import failure for `app.services.nixtla_client`

- [ ] **Step 3: Add minimal config fields and client implementation**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # existing fields...
    nixtla_api_base_url: str = "https://api.nixtla.io"
    nixtla_api_key: str | None = None
    nixtla_timeout_ms: int = 4000
```

```python
# backend/app/services/nixtla_client.py
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
            headers={"Authorization": f"Bearer {self._config.api_key}"},
            json=payload,
            timeout=self._config.timeout_ms / 1000,
        )
        response.raise_for_status()
        body = response.json()
        anomalies = body.get("anomaly") or []
        scores = body.get("scores") or []
        latest_flag = bool(anomalies[-1]) if anomalies else False
        score = float(scores[-1]) if scores else None
        return NixtlaAnomalyDetectionResult(has_anomaly=any(bool(item) for item in anomalies), latest_flag=latest_flag, score=score)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `..\.condaenv\python.exe -m pytest tests/test_nixtla_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/services/nixtla_client.py backend/tests/test_nixtla_client.py .env.example
git commit -m "feat: add nixtla anomaly client scaffolding"
```

### Task 2: Route anomaly detection through Nixtla with local fallback

**Files:**
- Modify: `D:\codex\job\backend\app\services\analysis_service.py`
- Modify: `D:\codex\job\backend\tests\test_analysis_service.py`

- [ ] **Step 1: Write the failing service tests**

```python
from app.schemas.analysis import AnalysisAnomalyRequest, AnalysisHourlyAirQualityPoint
from app.services.analysis_service import detect_anomaly
from app.services.nixtla_client import NixtlaAnomalyDetectionResult


class StubNixtlaClient:
    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error

    def detect_online_anomaly(self, hourly_points):
        if self._error:
            raise self._error
        return self._result


def test_detect_anomaly_uses_nixtla_result_when_available(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service._build_nixtla_client",
        lambda: StubNixtlaClient(result=NixtlaAnomalyDetectionResult(has_anomaly=True, latest_flag=True, score=0.91)),
    )

    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80, pm25=52.0),
                AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105, pm25=83.2),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.status == "ok"
    assert result.anomalyFlags == ["nixtla_online_anomaly"]


def test_detect_anomaly_falls_back_to_local_rules_when_nixtla_fails(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service._build_nixtla_client",
        lambda: StubNixtlaClient(error=RuntimeError("upstream unavailable")),
    )

    result = detect_anomaly(
        AnalysisAnomalyRequest(
            enableDetection=True,
            hourlyAirQuality=[
                AnalysisHourlyAirQualityPoint(time="2026-06-07T14:00:00Z", aqi=80),
                AnalysisHourlyAirQualityPoint(time="2026-06-07T15:00:00Z", aqi=105),
            ],
        )
    )

    assert result.hasAnomaly is True
    assert result.status == "degraded"
    assert result.anomalyFlags == ["aqi_spike"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `..\.condaenv\python.exe -m pytest tests/test_analysis_service.py -v`
Expected: FAIL because `detect_anomaly()` still returns the old local-only behavior

- [ ] **Step 3: Implement Nixtla-first logic with local fallback**

```python
# backend/app/services/analysis_service.py
from app.config import settings
from app.services.nixtla_client import (
    NixtlaClient,
    NixtlaConfig,
    NixtlaDisabledError,
)


def _build_nixtla_client() -> NixtlaClient:
    return NixtlaClient(
        config=NixtlaConfig(
            api_key=settings.nixtla_api_key,
            base_url=settings.nixtla_api_base_url,
            timeout_ms=settings.nixtla_timeout_ms,
        )
    )


def _detect_anomaly_with_local_rules(request: AnalysisAnomalyRequest, *, degraded: bool = False) -> AnomalyResult:
    # keep the existing local logic here
    ...


def detect_anomaly(request: AnalysisAnomalyRequest) -> AnomalyResult:
    if not request.enableDetection:
        return AnomalyResult(
            hasAnomaly=False,
            anomalyFlags=[],
            severity="none",
            messages=[],
            status="ok",
        )

    hourly = request.hourlyAirQuality
    if len(hourly) < 2:
        return _detect_anomaly_with_local_rules(request)

    try:
        nixtla_result = _build_nixtla_client().detect_online_anomaly(
            hourly_points=[
                {
                    "time": point.time,
                    "aqi": point.aqi,
                    "pm25": point.pm25,
                }
                for point in hourly
            ]
        )
        return AnomalyResult(
            hasAnomaly=nixtla_result.has_anomaly,
            anomalyFlags=["nixtla_online_anomaly"] if nixtla_result.latest_flag else [],
            severity="medium" if nixtla_result.latest_flag else "none",
            messages=["Nixtla 检测到最新监测窗口存在异常波动。"] if nixtla_result.latest_flag else [],
            status="ok",
        )
    except (NixtlaDisabledError, RuntimeError, httpx.HTTPError, ValueError):
        return _detect_anomaly_with_local_rules(request, degraded=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `..\.condaenv\python.exe -m pytest tests/test_analysis_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/analysis_service.py backend/tests/test_analysis_service.py
git commit -m "feat: route anomaly detection through nixtla with fallback"
```

### Task 3: Keep dashboard behavior compatible and fix parameter mismatch

**Files:**
- Modify: `D:\codex\job\backend\tests\test_dashboard_service.py`
- Modify: `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`
- Modify: `D:\codex\job\frontend\src\components\dashboard\__tests__\CitySelector.test.ts`

- [ ] **Step 1: Write the failing compatibility tests**

```python
# backend/tests/test_dashboard_service.py

def test_dashboard_service_marks_analysis_degraded_when_local_anomaly_fallback_is_used(monkeypatch):
    from app.services.nixtla_client import NixtlaDisabledError
    from app.services import analysis_service

    monkeypatch.setattr(
        analysis_service,
        "_build_nixtla_client",
        lambda: type("Stub", (), {"detect_online_anomaly": lambda self, hourly_points: (_ for _ in ()).throw(NixtlaDisabledError("missing api key"))})(),
    )

    service = DashboardService(upstream_client=StubUpstreamClient())
    result = service.query_dashboard(DashboardQueryRequest(city="Beijing"))

    assert result.anomaly.status == "degraded"
```

```ts
// frontend/src/components/dashboard/__tests__/CitySelector.test.ts
it('does not offer unsupported 10-day weather forecast option', () => {
  const wrapper = mount(CitySelector, {
    props: {
      modelValue: 'Beijing',
      forecastDays: 7,
      aqForecastDays: 5,
      enableAnomalyDetection: true,
    },
  })

  expect(wrapper.text()).not.toContain('10 天')
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `..\.condaenv\python.exe -m pytest tests/test_dashboard_service.py -v`
Expected: FAIL because dashboard still reports analysis `ok`

Run: `npm run test -- --run src/components/dashboard/__tests__/CitySelector.test.ts`
Expected: FAIL because `10 天` option still exists

- [ ] **Step 3: Apply the minimal compatibility fixes**

```python
# backend/app/services/dashboard_service.py
source_status_analysis = "ok" if anomaly.status == "ok" and risk.status == "ok" else "degraded"
```

```ts
// frontend/src/components/dashboard/CitySelector.vue
const forecastDayOptions = [3, 5, 7]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `..\.condaenv\python.exe -m pytest tests/test_dashboard_service.py -v`
Expected: PASS

Run: `npm run test -- --run src/components/dashboard/__tests__/CitySelector.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_dashboard_service.py backend/app/services/dashboard_service.py frontend/src/components/dashboard/CitySelector.vue frontend/src/components/dashboard/__tests__/CitySelector.test.ts
git commit -m "fix: align anomaly degradation status and forecast options"
```

### Task 4: Update docs and verify end-to-end behavior

**Files:**
- Modify: `D:\codex\job\README.md`
- Modify: `D:\codex\job\docs\03-api-spec.md`
- Modify: `D:\codex\job\.env.example`

- [ ] **Step 1: Add doc expectations as a checklist**

```markdown
- README mentions optional `NIXTLA_API_KEY`
- API spec states anomaly detection is third-party-first with local fallback
- .env.example contains `NIXTLA_API_BASE_URL`, `NIXTLA_API_KEY`, `NIXTLA_TIMEOUT_MS`
```

- [ ] **Step 2: Update the docs**

```env
NIXTLA_API_BASE_URL=https://api.nixtla.io
NIXTLA_API_KEY=
NIXTLA_TIMEOUT_MS=4000
```

```md
异常检测链路当前采用“Nixtla online anomaly detection 优先，本地规则降级兜底”的策略。
```

- [ ] **Step 3: Run the full verification suite**

Run: `..\.condaenv\python.exe -m pytest tests -v`
Expected: PASS

Run: `npm run test -- --run`
Expected: PASS

- [ ] **Step 4: Run a quick backend smoke check**

Run: `..\.condaenv\python.exe - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post('/api/v1/analysis/detect-anomaly', json={
    'enableDetection': True,
    'hourlyAirQuality': [
        {'time': '2026-06-07T14:00:00Z', 'aqi': 80},
        {'time': '2026-06-07T15:00:00Z', 'aqi': 105}
    ]
})
print(response.status_code)
print(response.json())
PY`
Expected: `200` plus a valid `AnomalyResult`

- [ ] **Step 5: Commit**

```bash
git add README.md docs/03-api-spec.md .env.example
git commit -m "docs: describe nixtla anomaly detection fallback flow"
```
