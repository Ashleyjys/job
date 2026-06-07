# 数据契约说明（Data Contract）

## 1. 文档目标
本文档用于冻结系统内外部数据结构，保证：
- 前后端字段一致
- 适配层与服务层边界清晰
- 测试样例可复用
- 后续扩展不破坏现有 MVP

## 2. 契约分层
### 2.1 外部原始数据契约
- Geocoding API 响应
- Weather API 响应
- Air Quality API 响应

### 2.2 内部标准化契约
- LocationInfo
- NormalizedWeather
- NormalizedAirQuality
- AnalysisWeatherInput
- AnalysisAirQualityInput
- AnalysisRulesInput
- AnalysisRiskRequest
- AnalysisHourlyAirQualityPoint
- AnalysisAnomalyRequest
- RiskScoreResult
- AnomalyResult

### 2.3 前端展示契约
- DashboardQueryRequest
- DashboardViewModel

## 3. 基础类型约定
| 名称 | 类型 | 说明 |
|---|---|---|
| `DateTimeISO` | string | ISO 8601 日期时间 |
| `DateISO` | string | YYYY-MM-DD |
| `Float` | number | 浮点数 |
| `Int` | integer | 整数 |
| `RiskLevel` | enum | `low` / `medium` / `high` / `unknown` |
| `SourceStatus` | enum | `ok` / `degraded` / `failed` |

## 4. 外部数据原始模型
### 4.1 GeocodingSearchResult
```json
{
  "results": [
    {
      "name": "Beijing",
      "latitude": 39.9075,
      "longitude": 116.3972,
      "country": "China",
      "timezone": "Asia/Shanghai",
      "admin1": "Beijing"
    }
  ]
}
```

### 4.2 WeatherForecastRaw
```json
{
  "latitude": 39.9,
  "longitude": 116.4,
  "timezone": "Asia/Shanghai",
  "current": {
    "time": "2026-06-07T14:00",
    "temperature_2m": 30.1,
    "relative_humidity_2m": 61,
    "wind_speed_10m": 3.8,
    "weather_code": 1
  },
  "hourly": {
    "time": ["2026-06-07T14:00"],
    "temperature_2m": [30.1],
    "relative_humidity_2m": [61],
    "wind_speed_10m": [3.8]
  },
  "daily": {
    "time": ["2026-06-07"],
    "temperature_2m_max": [34.2],
    "temperature_2m_min": [24.6],
    "wind_speed_10m_max": [5.2]
  }
}
```

### 4.3 AirQualityRaw
```json
{
  "latitude": 39.9,
  "longitude": 116.4,
  "timezone": "Asia/Shanghai",
  "current": {
    "time": "2026-06-07T14:00",
    "us_aqi": 118,
    "pm2_5": 82.4,
    "pm10": 120.2,
    "nitrogen_dioxide": 36.1,
    "ozone": 88.4
  },
  "hourly": {
    "time": ["2026-06-07T14:00"],
    "us_aqi": [118],
    "pm2_5": [82.4],
    "pm10": [120.2],
    "nitrogen_dioxide": [36.1],
    "ozone": [88.4]
  }
}
```

## 5. 内部标准化模型
### 5.1 LocationInfo
```ts
interface LocationInfo {
  name: string;
  country?: string;
  admin1?: string;
  latitude: number;
  longitude: number;
  timezone: string;
}
```

### 5.2 CurrentWeather
```ts
interface CurrentWeather {
  observedAt: string;
  temperature: number | null;
  humidity: number | null;
  windSpeed: number | null;
  weatherCode: number | null;
}
```

### 5.3 WeatherTrendPoint
```ts
interface WeatherTrendPoint {
  time: string;
  temperature: number | null;
  humidity: number | null;
  windSpeed: number | null;
}
```

### 5.4 DailyWeatherForecast
```ts
interface DailyWeatherForecast {
  date: string;
  maxTemperature: number | null;
  minTemperature: number | null;
  maxWindSpeed: number | null;
}
```

### 5.5 NormalizedWeather
```ts
interface NormalizedWeather {
  source: 'open-meteo-weather';
  status: 'ok' | 'degraded' | 'failed';
  location: LocationInfo;
  current: CurrentWeather | null;
  hourly: WeatherTrendPoint[];
  daily: DailyWeatherForecast[];
}
```

### 5.6 CurrentAirQuality
```ts
interface CurrentAirQuality {
  observedAt: string;
  aqi: number | null;
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  ozone: number | null;
}
```

### 5.7 AirQualityTrendPoint
```ts
interface AirQualityTrendPoint {
  time: string;
  aqi: number | null;
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  ozone: number | null;
}
```

### 5.8 NormalizedAirQuality
```ts
interface NormalizedAirQuality {
  source: 'open-meteo-air-quality';
  status: 'ok' | 'degraded' | 'failed';
  location: LocationInfo;
  current: CurrentAirQuality | null;
  hourly: AirQualityTrendPoint[];
}
```

### 5.9 AnalysisWeatherInput
```ts
interface AnalysisWeatherInput {
  temperature?: number | null;
  humidity?: number | null;
  windSpeed?: number | null;
  weatherCode?: number | null;
}
```

### 5.10 AnalysisAirQualityInput
```ts
interface AnalysisAirQualityInput {
  aqi?: number | null;
  pm2_5?: number | null;
  pm10?: number | null;
  no2?: number | null;
  ozone?: number | null;
}
```

### 5.11 AnalysisRulesInput
```ts
interface AnalysisRulesInput {
  highRiskThreshold?: number;
  mediumRiskThreshold?: number;
  aqiWeight?: number;
  pm25Weight?: number;
  weatherWeight?: number;
}
```

### 5.12 AnalysisRiskRequest
```ts
interface AnalysisRiskRequest {
  weather: AnalysisWeatherInput;
  airQuality: AnalysisAirQualityInput;
  rules?: AnalysisRulesInput | null;
}
```

### 5.13 AnalysisHourlyAirQualityPoint
```ts
interface AnalysisHourlyAirQualityPoint {
  time: string;
  aqi?: number | null;
  pm25?: number | null;
  pm10?: number | null;
  no2?: number | null;
  ozone?: number | null;
}
```

### 5.14 AnalysisAnomalyRequest
```ts
interface AnalysisAnomalyRequest {
  enableDetection?: boolean;
  hourlyAirQuality: AnalysisHourlyAirQualityPoint[];
}
```

### 5.15 RiskScoreResult
```ts
interface RiskScoreResult {
  riskScore: number | null;
  riskLevel: 'low' | 'medium' | 'high' | 'unknown';
  primaryFactors: string[];
  summary: string;
  status: 'ok' | 'degraded' | 'failed';
}
```

### 5.16 AnomalyResult
```ts
interface AnomalyResult {
  hasAnomaly: boolean;
  anomalyFlags: string[];
  severity: 'low' | 'medium' | 'high' | 'none';
  messages: string[];
  status: 'ok' | 'degraded' | 'failed';
}
```

## 6. 前端请求契约
### 6.1 DashboardQueryRequest
```ts
interface DashboardQueryRequest {
  city?: string;
  location?: {
    latitude: number;
    longitude: number;
    timezone?: string;
  };
  workflowId?: string;
  options?: {
    forecastDays?: number;
    aqForecastDays?: number;
    enableAnomalyDetection?: boolean;
  };
  riskRules?: {
    highRiskThreshold?: number;
    mediumRiskThreshold?: number;
    aqiWeight?: number;
    pm25Weight?: number;
    pm10Weight?: number;
    weatherWeight?: number;
  };
}
```

**校验规则**
- `city` 和 `location` 至少提供一个
- `forecastDays` 范围建议为 `1-7`
- `aqForecastDays` 范围建议为 `1-5`
- 所有权重之和建议为 `1`，不满足时后端可归一化处理

## 7. 前端展示契约
### 7.1 MetricCardItem
```ts
interface MetricCardItem {
  key: string;
  label: string;
  value: number | string | null;
  unit?: string;
  status?: 'normal' | 'warning' | 'danger' | 'unknown';
}
```

### 7.2 TrendSeries
```ts
interface TrendSeries {
  name: string;
  data: Array<{
    time: string;
    value: number | null;
  }>;
  unit?: string;
}
```

### 7.3 DataSourceStatus
```ts
interface DataSourceStatus {
  weather: 'ok' | 'degraded' | 'failed';
  airQuality: 'ok' | 'degraded' | 'failed';
  analysis: 'ok' | 'degraded' | 'failed';
}
```

### 7.4 DashboardViewModel
```ts
interface DashboardViewModel {
  traceId: string;
  workflowRunId: string;
  location: LocationInfo;
  currentMetrics: MetricCardItem[];
  weatherTrend: TrendSeries[];
  airQualityTrend: TrendSeries[];
  dailyForecast: DailyWeatherForecast[];
  risk: RiskScoreResult;
  anomaly: AnomalyResult;
  sourceStatus: DataSourceStatus;
  notices: string[];
  generatedAt: string;
}
```

## 8. 错误响应契约
```ts
interface ErrorResponse {
  code: string;
  message: string;
  traceId: string;
  details?: Record<string, unknown>;
}
```

## 9. 字段命名规范
- 前端与后端统一使用 camelCase
- 外部原始字段保持上游命名，仅在 adapter 层使用
- DTO 与 ViewModel 禁止混用 snake_case 和 camelCase

## 10. 版本兼容策略
- 现阶段冻结 MVP 的 `DashboardViewModel` 结构
- 新增字段尽量采用向后兼容方式添加
- 删除字段或变更字段语义时必须升级 API 版本
