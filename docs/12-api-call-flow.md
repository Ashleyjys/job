# 接口调用关系图

这张图说明当前项目里“前端 -> 后端 -> 外部数据接口 -> 页面展示”的实际调用链。

```mermaid
flowchart LR
    U[用户操作\n打开页面 / 提交城市] --> V[前端页面\nDashboardPage.vue]
    V --> C[查询逻辑\nuseDashboardQuery.ts]
    C --> A[前端接口封装\nqueryDashboard()\napi.ts]
    A --> P[Vite 开发代理\n/api -> localhost:8000]
    P --> F[FastAPI 应用\nmain.py]
    F --> R[看板接口\nPOST /api/v1/dashboard/query\nrouters/dashboard.py]
    R --> S[DashboardService.query_dashboard()\ndashboard_service.py]

    S --> W[加载工作流配置\nload_workflow()]
    S --> L{是否直接给经纬度?}
    L -- 是 --> LOC[使用请求里的 location]
    L -- 否 --> G[城市解析\nsearch_city()]
    G --> GEO[Open-Meteo Geocoding API]

    LOC --> M
    GEO --> M[确定城市坐标与时区]

    M --> FW[拉取天气数据\nfetch_weather()]
    M --> FA[拉取空气质量数据\nfetch_air_quality()]
    FW --> WEATHER[Open-Meteo Weather API]
    FA --> AIR[Open-Meteo Air Quality API]

    WEATHER --> N1[标准化天气数据]
    AIR --> N2[标准化空气质量数据]

    N1 --> AR[风险评分\nscore_risk()\nanalysis_service.py]
    N2 --> AR
    N2 --> AN[异常检测\ndetect_anomaly()\nanalysis_service.py]

    AR --> VM[组装统一返回模型\nDashboardViewModel]
    AN --> VM
    N1 --> VM
    N2 --> VM

    S --> FB{上游失败?}
    FB -- 是且开启 fallback --> MOCK[build_mock_dashboard_view_model()\n本地 Mock 数据]
    MOCK --> VM
    FB -- 否 --> VM

    VM --> FE[前端收到响应]
    FE --> MC[MetricCards\n当前指标卡片]
    FE --> RP[RiskPanel\n风险评分面板]
    FE --> SP[StatusPanel\n数据源状态 / 异常提示]
    FE --> TW[TrendChart\n天气趋势图]
    FE --> TA[TrendChart\n空气质量趋势图]
    FE --> DF[未来天气卡片\ndailyForecast]

    subgraph 独立分析接口[后端也额外提供但前端主流程暂未直接调用]
        X1[POST /api/v1/analysis/score-risk]
        X2[POST /api/v1/analysis/detect-anomaly]
    end
```

## 关键结论

- 前端当前真正调用的是统一看板接口：`POST /api/v1/dashboard/query`
- 风险评分与异常检测已经在使用，但目前是后端内部函数调用，不是前端单独请求分析接口
- 外部真实数据接口当前包括：
  - Open-Meteo Geocoding API
  - Open-Meteo Weather API
  - Open-Meteo Air Quality API
- 如果上游接口失败，且 `enable_mock_fallback=true`，后端会回退到本地 Mock 数据

## 对应代码位置

- 前端请求入口：`frontend/src/services/api.ts`
- 前端查询封装：`frontend/src/composables/useDashboardQuery.ts`
- 页面触发入口：`frontend/src/views/DashboardPage.vue`
- 后端看板接口：`backend/app/routers/dashboard.py`
- 后端编排主流程：`backend/app/services/dashboard_service.py`
- 外部接口适配：`backend/app/services/open_meteo_client.py`
- 分析逻辑：`backend/app/services/analysis_service.py`
- 后端应用入口：`backend/app/main.py`
