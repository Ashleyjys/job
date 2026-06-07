# Project Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the initial full-stack project skeleton for the air quality and weather dashboard, including Vue 3 frontend, FastAPI backend, workflow loading scaffold, and minimal tests.

**Architecture:** The frontend will use Vue 3 with Composition API and `<script setup lang="ts">`, organized by feature and thin page composition. The backend will use FastAPI with clear router/service/adapter/schema boundaries and a lightweight workflow loader for `workflows/main.yaml`. Both sides will start with a minimal vertical slice that proves the project structure, config loading, and a basic health/dashboard contract.

**Tech Stack:** Vue 3, TypeScript, Vite, FastAPI, Pydantic, pytest, Vitest, YAML

---

## File Structure Map

**Create:**
- `D:\codex\job\frontend\package.json`
- `D:\codex\job\frontend\tsconfig.json`
- `D:\codex\job\frontend\vite.config.ts`
- `D:\codex\job\frontend\index.html`
- `D:\codex\job\frontend\src\main.ts`
- `D:\codex\job\frontend\src\App.vue`
- `D:\codex\job\frontend\src\styles.css`
- `D:\codex\job\frontend\src\types\dashboard.ts`
- `D:\codex\job\frontend\src\services\api.ts`
- `D:\codex\job\frontend\src\composables\useDashboardQuery.ts`
- `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`
- `D:\codex\job\frontend\src\components\dashboard\MetricCards.vue`
- `D:\codex\job\frontend\src\components\dashboard\RiskPanel.vue`
- `D:\codex\job\frontend\src\components\dashboard\StatusPanel.vue`
- `D:\codex\job\frontend\src\views\DashboardPage.vue`
- `D:\codex\job\frontend\vitest.config.ts`
- `D:\codex\job\frontend\src\components\dashboard\__tests__\MetricCards.test.ts`
- `D:\codex\job\frontend\src\services\__tests__\api.test.ts`
- `D:\codex\job\backend\requirements.txt`
- `D:\codex\job\backend\app\main.py`
- `D:\codex\job\backend\app\config.py`
- `D:\codex\job\backend\app\schemas\dashboard.py`
- `D:\codex\job\backend\app\routers\health.py`
- `D:\codex\job\backend\app\routers\dashboard.py`
- `D:\codex\job\backend\app\services\workflow_loader.py`
- `D:\codex\job\backend\app\services\dashboard_service.py`
- `D:\codex\job\backend\app\services\mock_dashboard_data.py`
- `D:\codex\job\backend\tests\test_health.py`
- `D:\codex\job\backend\tests\test_workflow_loader.py`
- `D:\codex\job\backend\tests\test_dashboard_router.py`

**Modify:**
- `D:\codex\job\README.md`
- `D:\codex\job\.env.example`
- `D:\codex\job\docs\10-deployment-runbook.md`
- `D:\codex\job\docs\11-delivery-checklist.md`

---

### Task 1: Scaffold backend config and health slice

**Files:**
- Create: `D:\codex\job\backend\requirements.txt`
- Create: `D:\codex\job\backend\app\config.py`
- Create: `D:\codex\job\backend\app\main.py`
- Create: `D:\codex\job\backend\app\routers\health.py`
- Test: `D:\codex\job\backend\tests\test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest D:\codex\job\backend\tests\test_health.py -v`
Expected: FAIL because `app.main` or `app` is missing

- [ ] **Step 3: Write minimal backend skeleton**

```python
# D:\codex\job\backend\app\config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    api_base_url: str = "http://localhost:8000"
    workflow_id: str = "main"


settings = Settings()
```

```python
# D:\codex\job\backend\app\routers\health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# D:\codex\job\backend\app\main.py
from fastapi import FastAPI
from app.routers.health import router as health_router

app = FastAPI(title="Air Quality Weather Dashboard API")
app.include_router(health_router)
```

```text
# D:\codex\job\backend\requirements.txt
fastapi==0.116.1
uvicorn==0.35.0
pydantic==2.11.7
pydantic-settings==2.10.1
pytest==8.4.1
httpx==0.28.1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest D:\codex\job\backend\tests\test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/config.py backend/app/main.py backend/app/routers/health.py backend/tests/test_health.py
git commit -m "feat: add backend health skeleton"
```

### Task 2: Add workflow loader with YAML-backed test

**Files:**
- Create: `D:\codex\job\backend\app\services\workflow_loader.py`
- Test: `D:\codex\job\backend\tests\test_workflow_loader.py`
- Use existing: `D:\codex\job\workflows\main.yaml`

- [ ] **Step 1: Write the failing workflow loader test**

```python
from app.services.workflow_loader import load_workflow


def test_load_workflow_returns_main_workflow_definition():
    workflow = load_workflow("main")

    assert workflow["id"] == "main"
    assert workflow["name"] == "air-quality-weather-dashboard"
    assert len(workflow["steps"]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest D:\codex\job\backend\tests\test_workflow_loader.py -v`
Expected: FAIL because `load_workflow` does not exist

- [ ] **Step 3: Write minimal workflow loader**

```python
# D:\codex\job\backend\app\services\workflow_loader.py
from pathlib import Path
import yaml


WORKFLOW_DIR = Path(__file__).resolve().parents[3] / "workflows"


def load_workflow(workflow_id: str) -> dict:
    workflow_path = WORKFLOW_DIR / f"{workflow_id}.yaml"
    with workflow_path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)
```

- [ ] **Step 4: Update backend requirements to include YAML support**

```text
# append to D:\codex\job\backend\requirements.txt
PyYAML==6.0.2
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest D:\codex\job\backend\tests\test_workflow_loader.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/workflow_loader.py backend/tests/test_workflow_loader.py backend/requirements.txt workflows/main.yaml
git commit -m "feat: add workflow loader service"
```

### Task 3: Add minimal dashboard contract endpoint

**Files:**
- Create: `D:\codex\job\backend\app\schemas\dashboard.py`
- Create: `D:\codex\job\backend\app\services\mock_dashboard_data.py`
- Create: `D:\codex\job\backend\app\services\dashboard_service.py`
- Create: `D:\codex\job\backend\app\routers\dashboard.py`
- Test: `D:\codex\job\backend\tests\test_dashboard_router.py`
- Modify: `D:\codex\job\backend\app\main.py`

- [ ] **Step 1: Write the failing dashboard endpoint test**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_query_returns_minimal_view_model():
    response = client.post(
        "/api/v1/dashboard/query",
        json={"city": "Beijing", "workflowId": "main"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"]["name"] == "Beijing"
    assert "risk" in data
    assert "sourceStatus" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest D:\codex\job\backend\tests\test_dashboard_router.py -v`
Expected: FAIL because route does not exist

- [ ] **Step 3: Write minimal schemas and service**

```python
# D:\codex\job\backend\app\schemas\dashboard.py
from pydantic import BaseModel


class DashboardQueryRequest(BaseModel):
    city: str
    workflowId: str = "main"


class LocationInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone: str


class RiskResult(BaseModel):
    riskScore: int
    riskLevel: str
    summary: str
    primaryFactors: list[str]
    status: str


class SourceStatus(BaseModel):
    weather: str
    airQuality: str
    analysis: str


class DashboardViewModel(BaseModel):
    traceId: str
    workflowRunId: str
    location: LocationInfo
    currentMetrics: list[dict]
    weatherTrend: list[dict]
    airQualityTrend: list[dict]
    dailyForecast: list[dict]
    risk: RiskResult
    anomaly: dict
    sourceStatus: SourceStatus
    notices: list[str]
    generatedAt: str
```

```python
# D:\codex\job\backend\app\services\mock_dashboard_data.py
from datetime import datetime, UTC


def build_mock_dashboard(city: str) -> dict:
    return {
        "traceId": "trace-local-001",
        "workflowRunId": "run-local-001",
        "location": {
            "name": city,
            "latitude": 39.9042,
            "longitude": 116.4074,
            "timezone": "Asia/Shanghai",
        },
        "currentMetrics": [
            {"key": "aqi", "label": "AQI", "value": 118, "unit": "index", "status": "warning"}
        ],
        "weatherTrend": [],
        "airQualityTrend": [],
        "dailyForecast": [],
        "risk": {
            "riskScore": 76,
            "riskLevel": "high",
            "summary": "当前空气质量和颗粒物浓度较高，综合风险偏高。",
            "primaryFactors": ["aqi", "pm25"],
            "status": "ok",
        },
        "anomaly": {
            "hasAnomaly": False,
            "anomalyFlags": [],
            "severity": "none",
            "messages": [],
            "status": "ok",
        },
        "sourceStatus": {"weather": "ok", "airQuality": "ok", "analysis": "ok"},
        "notices": [],
        "generatedAt": datetime.now(UTC).isoformat(),
    }
```

```python
# D:\codex\job\backend\app\services\dashboard_service.py
from app.services.mock_dashboard_data import build_mock_dashboard
from app.services.workflow_loader import load_workflow


class DashboardService:
    def query_dashboard(self, city: str, workflow_id: str) -> dict:
        load_workflow(workflow_id)
        return build_mock_dashboard(city)
```

```python
# D:\codex\job\backend\app\routers\dashboard.py
from fastapi import APIRouter
from app.schemas.dashboard import DashboardQueryRequest, DashboardViewModel
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
service = DashboardService()


@router.post("/query", response_model=DashboardViewModel)
def query_dashboard(payload: DashboardQueryRequest) -> DashboardViewModel:
    result = service.query_dashboard(payload.city, payload.workflowId)
    return DashboardViewModel(**result)
```

```python
# modify D:\codex\job\backend\app\main.py
from app.routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest D:\codex\job\backend\tests\test_dashboard_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/dashboard.py backend/app/services/mock_dashboard_data.py backend/app/services/dashboard_service.py backend/app/routers/dashboard.py backend/app/main.py backend/tests/test_dashboard_router.py
git commit -m "feat: add dashboard query skeleton"
```

### Task 4: Scaffold Vue frontend with typed API client

**Files:**
- Create: `D:\codex\job\frontend\package.json`
- Create: `D:\codex\job\frontend\tsconfig.json`
- Create: `D:\codex\job\frontend\vite.config.ts`
- Create: `D:\codex\job\frontend\index.html`
- Create: `D:\codex\job\frontend\src\main.ts`
- Create: `D:\codex\job\frontend\src\App.vue`
- Create: `D:\codex\job\frontend\src\styles.css`
- Create: `D:\codex\job\frontend\src\types\dashboard.ts`
- Create: `D:\codex\job\frontend\src\services\api.ts`
- Test: `D:\codex\job\frontend\src\services\__tests__\api.test.ts`

- [ ] **Step 1: Write the failing API client test**

```ts
import { describe, expect, it } from 'vitest'
import { createApiUrl } from '../api'

describe('createApiUrl', () => {
  it('builds dashboard query url from base url and path', () => {
    expect(createApiUrl('http://localhost:8000', '/api/v1/dashboard/query')).toBe(
      'http://localhost:8000/api/v1/dashboard/query',
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:\codex\job\frontend; npm run test -- src/services/__tests__/api.test.ts`
Expected: FAIL because frontend project and `createApiUrl` do not exist

- [ ] **Step 3: Write minimal Vue app and API client**

```json
// D:\codex\job\frontend\package.json
{
  "name": "air-quality-weather-dashboard-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "vue": "^3.5.18"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.1",
    "typescript": "^5.8.3",
    "vite": "^7.0.6",
    "vitest": "^3.2.4"
  }
}
```

```ts
// D:\codex\job\frontend\src\services\api.ts
export function createApiUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/$/, '')}${path}`
}
```

```ts
// D:\codex\job\frontend\src\main.ts
import { createApp } from 'vue'
import App from './App.vue'
import './styles.css'

createApp(App).mount('#app')
```

```vue
<!-- D:\codex\job\frontend\src\App.vue -->
<script setup lang="ts">
import DashboardPage from './views/DashboardPage.vue'
</script>

<template>
  <DashboardPage />
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\codex\job\frontend; npm run test -- src/services/__tests__/api.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/vite.config.ts frontend/index.html frontend/src/main.ts frontend/src/App.vue frontend/src/styles.css frontend/src/services/api.ts frontend/src/services/__tests__/api.test.ts
git commit -m "feat: add frontend vite vue skeleton"
```

### Task 5: Build thin Vue dashboard page and components

**Files:**
- Create: `D:\codex\job\frontend\src\types\dashboard.ts`
- Create: `D:\codex\job\frontend\src\composables\useDashboardQuery.ts`
- Create: `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`
- Create: `D:\codex\job\frontend\src\components\dashboard\MetricCards.vue`
- Create: `D:\codex\job\frontend\src\components\dashboard\RiskPanel.vue`
- Create: `D:\codex\job\frontend\src\components\dashboard\StatusPanel.vue`
- Create: `D:\codex\job\frontend\src\views\DashboardPage.vue`
- Test: `D:\codex\job\frontend\src\components\dashboard\__tests__\MetricCards.test.ts`

- [ ] **Step 1: Write the failing metric cards test**

```ts
import { describe, expect, it } from 'vitest'
import { renderToString } from 'vue/server-renderer'
import { createSSRApp } from 'vue'
import MetricCards from '../MetricCards.vue'

describe('MetricCards', () => {
  it('renders metric labels and values', async () => {
    const app = createSSRApp(MetricCards, {
      metrics: [{ key: 'aqi', label: 'AQI', value: 118, unit: 'index' }],
    })

    const html = await renderToString(app)
    expect(html).toContain('AQI')
    expect(html).toContain('118')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:\codex\job\frontend; npm run test -- src/components/dashboard/__tests__/MetricCards.test.ts`
Expected: FAIL because component does not exist

- [ ] **Step 3: Write minimal typed dashboard UI**

```ts
// D:\codex\job\frontend\src\types\dashboard.ts
export interface MetricCardItem {
  key: string
  label: string
  value: number | string | null
  unit?: string
  status?: 'normal' | 'warning' | 'danger' | 'unknown'
}

export interface DashboardViewModel {
  location: { name: string; latitude: number; longitude: number; timezone: string }
  currentMetrics: MetricCardItem[]
  risk: { riskScore: number; riskLevel: string; summary: string }
  notices: string[]
}
```

```ts
// D:\codex\job\frontend\src\composables\useDashboardQuery.ts
import { ref } from 'vue'
import type { DashboardViewModel } from '../types/dashboard'

const mockData: DashboardViewModel = {
  location: { name: 'Beijing', latitude: 39.9042, longitude: 116.4074, timezone: 'Asia/Shanghai' },
  currentMetrics: [{ key: 'aqi', label: 'AQI', value: 118, unit: 'index', status: 'warning' }],
  risk: { riskScore: 76, riskLevel: 'high', summary: '当前空气质量和颗粒物浓度较高，综合风险偏高。' },
  notices: [],
}

export function useDashboardQuery() {
  const dashboard = ref<DashboardViewModel | null>(mockData)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function loadDashboard(_city: string) {
    isLoading.value = true
    error.value = null
    dashboard.value = mockData
    isLoading.value = false
  }

  return { dashboard, isLoading, error, loadDashboard }
}
```

```vue
<!-- D:\codex\job\frontend\src\components\dashboard\MetricCards.vue -->
<script setup lang="ts">
import type { MetricCardItem } from '../../types/dashboard'

defineProps<{ metrics: MetricCardItem[] }>()
</script>

<template>
  <section class="metric-grid">
    <article v-for="metric in metrics" :key="metric.key" class="metric-card">
      <p class="metric-label">{{ metric.label }}</p>
      <p class="metric-value">{{ metric.value }} <span v-if="metric.unit">{{ metric.unit }}</span></p>
    </article>
  </section>
</template>
```

```vue
<!-- D:\codex\job\frontend\src\components\dashboard\CitySelector.vue -->
<script setup lang="ts">
const city = defineModel<string>({ required: true })
</script>

<template>
  <label class="city-selector">
    <span>城市</span>
    <input v-model="city" placeholder="请输入城市名" />
  </label>
</template>
```

```vue
<!-- D:\codex\job\frontend\src\components\dashboard\RiskPanel.vue -->
<script setup lang="ts">
defineProps<{ riskScore: number; riskLevel: string; summary: string }>()
</script>

<template>
  <section class="panel">
    <h2>风险评分</h2>
    <p>{{ riskScore }}</p>
    <p>{{ riskLevel }}</p>
    <p>{{ summary }}</p>
  </section>
</template>
```

```vue
<!-- D:\codex\job\frontend\src\components\dashboard\StatusPanel.vue -->
<script setup lang="ts">
defineProps<{ notices: string[] }>()
</script>

<template>
  <section class="panel">
    <h2>状态提示</h2>
    <p v-if="notices.length === 0">当前没有额外提示。</p>
    <ul v-else>
      <li v-for="notice in notices" :key="notice">{{ notice }}</li>
    </ul>
  </section>
</template>
```

```vue
<!-- D:\codex\job\frontend\src\views\DashboardPage.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CitySelector from '../components/dashboard/CitySelector.vue'
import MetricCards from '../components/dashboard/MetricCards.vue'
import RiskPanel from '../components/dashboard/RiskPanel.vue'
import StatusPanel from '../components/dashboard/StatusPanel.vue'
import { useDashboardQuery } from '../composables/useDashboardQuery'

const city = ref('Beijing')
const { dashboard, isLoading, error, loadDashboard } = useDashboardQuery()

onMounted(async () => {
  await loadDashboard(city.value)
})
</script>

<template>
  <main class="page-shell">
    <h1>空气质量 / 天气联动分析看板</h1>
    <CitySelector v-model="city" />
    <p v-if="isLoading">加载中...</p>
    <p v-else-if="error">{{ error }}</p>
    <template v-else-if="dashboard">
      <MetricCards :metrics="dashboard.currentMetrics" />
      <RiskPanel :risk-score="dashboard.risk.riskScore" :risk-level="dashboard.risk.riskLevel" :summary="dashboard.risk.summary" />
      <StatusPanel :notices="dashboard.notices" />
    </template>
  </main>
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:\codex\job\frontend; npm run test -- src/components/dashboard/__tests__/MetricCards.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/dashboard.ts frontend/src/composables/useDashboardQuery.ts frontend/src/components/dashboard/CitySelector.vue frontend/src/components/dashboard/MetricCards.vue frontend/src/components/dashboard/RiskPanel.vue frontend/src/components/dashboard/StatusPanel.vue frontend/src/views/DashboardPage.vue frontend/src/components/dashboard/__tests__/MetricCards.test.ts
git commit -m "feat: add dashboard page skeleton"
```

### Task 6: Update root docs and onboarding files

**Files:**
- Modify: `D:\codex\job\README.md`
- Modify: `D:\codex\job\.env.example`
- Modify: `D:\codex\job\docs\10-deployment-runbook.md`
- Modify: `D:\codex\job\docs\11-delivery-checklist.md`

- [ ] **Step 1: Add backend and frontend run instructions to README**

```md
## 本地启动（骨架阶段）
- 后端：进入 `backend/`，安装依赖后启动 FastAPI 应用
- 前端：进入 `frontend/`，安装依赖后启动 Vite 开发服务
- 当前骨架阶段默认返回本地 mock 看板数据
```

- [ ] **Step 2: Add frontend and backend-specific env notes**

```env
# Frontend build-time env
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 3: Update deployment runbook with skeleton verification**

```md
## 骨架阶段验证
1. `GET /health` 返回 `{ "status": "ok" }`
2. `POST /api/v1/dashboard/query` 返回最小看板视图模型
3. 前端页面可展示城市、AQI 卡片和风险面板
```

- [ ] **Step 4: Update delivery checklist for skeleton completion**

```md
- [ ] 已创建 `frontend/` Vue 3 + Vite 工程骨架
- [ ] 已创建 `backend/` FastAPI 工程骨架
- [ ] 已验证工作流配置文件可被后端加载
- [ ] 已验证前后端最小链路可运行
```

- [ ] **Step 5: Commit**

```bash
git add README.md .env.example docs/10-deployment-runbook.md docs/11-delivery-checklist.md
git commit -m "docs: add project skeleton onboarding"
```

## Self-Review
- Spec coverage: This plan covers project skeleton creation for frontend, backend, workflow loading, minimal contract endpoint, and documentation updates. It does not yet implement real upstream adapters, ECharts charts, or production analysis logic, which remain for later feature plans.
- Placeholder scan: No TODO/TBD placeholders remain in executable steps.
- Type consistency: Frontend and backend both use the same dashboard concepts (`location`, `currentMetrics`, `risk`, `notices`), and the backend workflow loader references `workflows/main.yaml` consistently.