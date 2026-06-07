# 接口规格说明（API Spec）

## 1. 文档目标
本文档定义“空气质量 / 天气联动分析看板”项目在 MVP 阶段使用的：
- 外部数据接口
- 内部算法接口
- 前后端统一访问接口
- 错误处理与降级策略

本文档用于冻结接口边界，避免前后端并行开发时出现字段漂移。

## 2. 接口分类
### 2.1 外部数据接口
- 地理编码接口：根据城市名搜索坐标
- 天气预报接口：获取当前、小时级和天级天气信息
- 空气质量接口：获取当前、小时级空气质量信息

### 2.2 内部算法接口
- 独立算法服务风险评分接口：根据天气与空气质量数据输出综合风险评分
- 独立算法服务异常检测接口：识别极值、突变和联动异常

### 2.3 前端访问接口
- 看板查询接口：由前端调用，后端编排完成数据获取、分析和视图模型组装
- 城市搜索接口：供前端搜索候选城市并回填坐标信息

## 3. 外部数据接口定义

### 3.1 地理编码接口
**用途**
- 将用户输入的城市名转换为坐标，供天气和空气质量接口使用。

**来源**
- Open-Meteo Geocoding API

**URL**
- `https://geocoding-api.open-meteo.com/v1/search`

**Method**
- `GET`

**核心请求参数**
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 城市名或邮编 |
| `count` | integer | 否 | 当前项目默认请求 8 条候选结果 |
| `language` | string | 否 | 返回语言，建议 `zh` 或 `en` |
| `format` | string | 否 | 建议使用 `json` |

**示例请求**
`GET /v1/search?name=Beijing&count=5&language=zh&format=json`

**关键响应字段**
| 字段 | 类型 | 说明 |
|---|---|---|
| `results[]` | array | 匹配地点列表 |
| `results[].name` | string | 地点名称 |
| `results[].latitude` | number | 纬度 |
| `results[].longitude` | number | 经度 |
| `results[].country` | string | 国家 |
| `results[].timezone` | string | 时区 |
| `results[].admin1` | string | 省/州 |

**鉴权方式**
- 无需 API Key（非商业场景）

**超时策略**
- 当前实现为 10 秒

**重试策略**
- 当前实现不重试，由上层调用方决定是否降级

**错误场景**
- 搜索词为空或过短
- 无匹配结果
- 上游超时或限流

**Mock / Fallback 方案**
- `OpenMeteoClient.search_city()` 当前不提供独立城市列表兜底。
- 若该步骤发生在看板查询链路中，且 `ENABLE_MOCK_FALLBACK=true`，后端会回退为整页 mock 看板结果，而不是单独回退城市坐标。

---

### 3.2 天气预报接口
**用途**
- 获取指定坐标的当前天气、24 小时趋势和未来 7 天预测摘要。

**来源**
- Open-Meteo Weather Forecast API

**URL**
- `https://api.open-meteo.com/v1/forecast`

**Method**
- `GET`

**核心请求参数**
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `latitude` | number | 是 | 纬度 |
| `longitude` | number | 是 | 经度 |
| `current` | string | 否 | 当前变量列表 |
| `hourly` | string | 否 | 小时级变量列表 |
| `daily` | string | 否 | 天级变量列表 |
| `timezone` | string | 否 | 建议 `auto` |
| `forecast_days` | integer | 否 | 预测天数，MVP 取 7 |

**建议变量**
- `current`：`temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code`
- `hourly`：`temperature_2m,relative_humidity_2m,wind_speed_10m`
- `daily`：`temperature_2m_max,temperature_2m_min,wind_speed_10m_max`

**示例请求**
`GET /v1/forecast?latitude=39.90&longitude=116.40&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,wind_speed_10m_max&timezone=auto&forecast_days=7`

**关键响应字段**
| 字段 | 类型 | 说明 |
|---|---|---|
| `latitude` | number | 请求位置 |
| `longitude` | number | 请求位置 |
| `timezone` | string | 返回时区 |
| `current` | object | 当前天气 |
| `hourly.time[]` | array | 小时级时间序列 |
| `hourly.temperature_2m[]` | array | 小时温度 |
| `hourly.relative_humidity_2m[]` | array | 小时湿度 |
| `hourly.wind_speed_10m[]` | array | 小时风速 |
| `daily.time[]` | array | 天级日期 |
| `daily.temperature_2m_max[]` | array | 日最高温 |
| `daily.temperature_2m_min[]` | array | 日最低温 |

**鉴权方式**
- 无需 API Key（非商业场景）

**超时策略**
- 5 秒

**重试策略**
- 当前实现不重试

**错误场景**
- 参数非法
- 上游超时
- 返回字段缺失
- 网络异常

**Mock / Fallback 方案**
- 当前天气客户端自身不直接返回局部样本。
- 在看板查询链路中，若天气或空气质量任一上游请求失败，且 `ENABLE_MOCK_FALLBACK=true`，后端会回退为整页 mock 看板结果。

---

### 3.3 空气质量接口
**用途**
- 获取指定坐标的当前 AQI 与小时级污染物趋势。

**来源**
- Open-Meteo Air Quality API

**URL**
- `https://air-quality-api.open-meteo.com/v1/air-quality`

**Method**
- `GET`

**核心请求参数**
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `latitude` | number | 是 | 纬度 |
| `longitude` | number | 是 | 经度 |
| `current` | string | 否 | 当前变量列表 |
| `hourly` | string | 否 | 小时级变量列表 |
| `timezone` | string | 否 | 建议 `auto` |
| `forecast_days` | integer | 否 | 预测天数，MVP 取 5 |
| `domains` | string | 否 | 默认 `auto` |

**建议变量**
- `current`：`us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone`
- `hourly`：`us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone`

**示例请求**
`GET /v1/air-quality?latitude=39.90&longitude=116.40&current=us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone&hourly=us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone&timezone=auto&forecast_days=5&domains=auto`

**关键响应字段**
| 字段 | 类型 | 说明 |
|---|---|---|
| `latitude` | number | 请求位置 |
| `longitude` | number | 请求位置 |
| `timezone` | string | 返回时区 |
| `current` | object | 当前空气质量 |
| `hourly.time[]` | array | 小时级时间序列 |
| `hourly.us_aqi[]` | array | 美国 AQI |
| `hourly.pm2_5[]` | array | PM2.5 |
| `hourly.pm10[]` | array | PM10 |
| `hourly.nitrogen_dioxide[]` | array | NO2 |
| `hourly.ozone[]` | array | O3 |

**鉴权方式**
- 无需 API Key（非商业场景）

**超时策略**
- 5 秒

**重试策略**
- 当前实现不重试

**错误场景**
- 参数非法
- 当前变量缺失
- 上游超时
- 返回时间序列长度不一致

**Mock / Fallback 方案**
- 当前空气质量客户端自身不直接返回局部样本。
- 在看板查询链路中，若天气或空气质量任一上游请求失败，且 `ENABLE_MOCK_FALLBACK=true`，后端会回退为整页 mock 看板结果，并返回 `sourceStatus=degraded`。

## 4. 内部算法接口定义

### 4.1 风险评分接口
**用途**
- 根据天气和空气质量标准化数据输出综合风险评分与等级。

**URL**
- `POST http://localhost:8100/score-risk`

**Method**
- `POST`

**请求体**
`application/json`

```json
{
  "weather": {
    "temperature": 30.1,
    "humidity": 61,
    "windSpeed": 3.8,
    "weatherCode": 1
  },
  "airQuality": {
    "aqi": 118,
    "pm2_5": 82.4,
    "pm10": 120.2,
    "no2": 36.1,
    "ozone": 88.4
  },
  "rules": {
    "aqiWeight": 0.45,
    "pm25Weight": 0.35,
    "weatherWeight": 0.2,
    "highRiskThreshold": 70,
    "mediumRiskThreshold": 40
  }
}
```

**说明**
- 看板查询接口传入 `riskRules` 时，后端会将 `highRiskThreshold`、`mediumRiskThreshold`、`aqiWeight`、`pm25Weight`、`pm10Weight`、`weatherWeight` 组装进该接口的 `rules` 字段。

**响应体**
```json
{
  "riskScore": 76,
  "riskLevel": "high",
  "primaryFactors": ["aqi", "pm25"],
  "summary": "AQI 与 PM2.5 偏高，建议减少长时间户外活动并关注后续变化。",
  "status": "ok"
}
```

**状态码**
- `200`：成功
- `422`：请求体校验失败

**超时策略**
- 默认 2 秒，实际由工作流配置 `analysisTimeoutMs` 驱动

**重试策略**
- 默认不重试，避免重复计算引发额外复杂性

**Mock / Fallback 方案**
- 启用本地规则引擎，以简单分段评分代替完整版算法服务。

---

### 4.2 异常检测接口
**用途**
- 检测污染物极值、突变和天气/AQI 联动异常。

**URL**
- `POST http://localhost:8100/detect-anomaly`

**Method**
- `POST`

**请求体**
```json
{
  "enableDetection": true,
  "hourlyAirQuality": [
    {
      "time": "2026-06-07T14:00:00Z",
      "aqi": 80,
      "pm25": 52.0
    },
    {
      "time": "2026-06-07T15:00:00Z",
      "aqi": 105,
      "pm25": 83.2
    }
  ]
}
```

**响应体**
```json
{
  "hasAnomaly": true,
  "anomalyFlags": ["aqi_spike"],
  "severity": "medium",
  "messages": [
    "最近监测窗口内 AQI 上升较快。"
  ],
  "status": "ok"
}
```

**状态码**
- `200`：成功
- `422`：请求体校验失败

## 5. 前端统一访问接口

### 5.1 看板查询接口
**用途**
- 提供给前端的单一入口，内部完成地理编码、天气/AQI 获取、独立算法服务调用和视图模型组装。

**URL**
- `POST /api/v1/dashboard/query`

**Method**
- `POST`

**请求体**
```json
{
  "city": "Beijing",
  "location": {
    "latitude": 39.9,
    "longitude": 116.4,
    "timezone": "Asia/Shanghai"
  },
  "workflowId": "main",
  "options": {
    "forecastDays": 7,
    "aqForecastDays": 5,
    "enableAnomalyDetection": true
  },
  "riskRules": {
    "aqiWeight": 0.45,
    "pm25Weight": 0.35,
    "pm10Weight": 0.1,
    "weatherWeight": 0.2,
    "highRiskThreshold": 70,
    "mediumRiskThreshold": 40
  }
}
```

**说明**
- `riskRules` 中的阈值会覆盖工作流默认阈值。
- `riskRules` 中当前已支持的权重参数会透传至算法服务：`aqiWeight`、`pm25Weight`、`pm10Weight`、`weatherWeight`。
- 后端会基于 `workflowId` 读取工作流配置，其中 `analysisTimeoutMs` 用于控制远端算法服务调用超时。

**响应体**
- 详见 `docs/06-data-contract.md` 中的 `DashboardViewModel`

**状态码**
- `200`：成功
- `422`：请求体校验失败
- `500`：后端编排失败

---

### 5.2 城市搜索接口
**用途**
- 为前端搜索框提供城市候选项，返回标准化地点信息列表。

**URL**
- `GET /api/v1/locations/search`

**Method**
- `GET`

**查询参数**
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `q` | string | 是 | 城市关键词 |
| `count` | integer | 否 | 最大候选数量，默认 `8`，上限 `10` |

**示例请求**
`GET /api/v1/locations/search?q=成都&count=8`

**响应体**
```json
[
  {
    "name": "成都",
    "country": "中国",
    "admin1": "四川",
    "latitude": 30.5728,
    "longitude": 104.0668,
    "timezone": "Asia/Shanghai"
  }
]
```

**状态码**
- `200`：成功
- `422`：查询参数校验失败
- `502`：地理编码上游不可用

## 6. 当前错误响应行为
- `POST /api/v1/dashboard/query`
  - 成功时返回 `DashboardViewModel`
  - 当地理编码或上游数据请求失败且 `ENABLE_MOCK_FALLBACK=true` 时，直接返回降级后的 mock 看板结果
  - 当前未实现统一的企业级错误信封结构
- `GET /api/v1/locations/search`
  - 上游不可用时返回 `502`，错误体为 FastAPI 默认结构，`detail` 为 `"Location search upstream unavailable."`
- 通用请求体校验失败时，使用 FastAPI 默认 `422` 响应结构

## 7. 降级策略
- 地理编码失败：若 `ENABLE_MOCK_FALLBACK=true`，返回整页 mock 看板；否则返回错误
- 天气或 AQI 任一上游失败：若 `ENABLE_MOCK_FALLBACK=true`，返回整页 mock 看板；当前不提供“天气成功 / AQI 失败”的局部展示模式
- 算法服务失败：对风险评分与异常检测统一回退到 `backend` 本地规则，`analysis` 状态标记为 `degraded`，不影响天气与 AQI 数据展示
- 异常检测关闭：当前仍会构造异常检测请求或本地检测输入，但通过 `enableDetection=false` 让检测结果返回“无异常”

## 8. 接口版本策略
- 前缀统一使用 `/api/v1`
- 外部上游版本由适配层管理，避免直接暴露到前端
- 当展示模型字段发生不兼容变化时，新开 `v2`，不破坏现有 `v1`
