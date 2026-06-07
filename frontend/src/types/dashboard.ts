export interface MetricCardItem {
  key: string
  label: string
  value: number | string | null
  unit?: string
  status?: 'normal' | 'warning' | 'danger' | 'unknown'
  trendDirection?: 'up' | 'down' | 'flat' | 'unknown'
  trendBadge?: string
  trendSummary?: string
  insight?: string
}

export interface TrendPoint {
  time: string
  value: number | null
}

export interface TrendSeries {
  name: string
  data: TrendPoint[]
  unit?: string
}

export interface DailyWeatherForecast {
  date: string
  maxTemperature: number | null
  minTemperature: number | null
  maxWindSpeed: number | null
}

export interface RiskScoreResult {
  riskScore: number | null
  riskLevel: 'low' | 'medium' | 'high' | 'unknown'
  primaryFactors: string[]
  summary: string
  status: 'ok' | 'degraded' | 'failed'
}

export interface AnomalyResult {
  hasAnomaly: boolean
  anomalyFlags: string[]
  severity: 'none' | 'low' | 'medium' | 'high'
  messages: string[]
  status: 'ok' | 'degraded' | 'failed'
}

export interface DataSourceStatus {
  weather: 'ok' | 'degraded' | 'failed'
  airQuality: 'ok' | 'degraded' | 'failed'
  analysis: 'ok' | 'degraded' | 'failed'
}

export interface LocationInfo {
  name: string
  country?: string
  admin1?: string | null
  latitude: number
  longitude: number
  timezone: string
}

export interface LocationSearchResult extends LocationInfo {}

export interface CityOption {
  label: string
  value: string
  location: LocationSearchResult
  badge?: string
}

export type CitySearchStatus = 'idle' | 'loading' | 'empty' | 'error'

export interface DashboardViewModel {
  traceId: string
  workflowRunId: string
  location: LocationInfo
  currentMetrics: MetricCardItem[]
  weatherTrend: TrendSeries[]
  airQualityTrend: TrendSeries[]
  dailyForecast: DailyWeatherForecast[]
  risk: RiskScoreResult
  anomaly: AnomalyResult
  sourceStatus: DataSourceStatus
  notices: string[]
  generatedAt: string
}

export interface DashboardQueryFormValues {
  city: string
  forecastDays: number
  aqForecastDays: number
  enableAnomalyDetection: boolean
  pm10Weight?: number | null
  selectedLocation?: LocationSearchResult | null
}

export interface DashboardQueryPayload {
  city?: string
  location?: {
    latitude: number
    longitude: number
    timezone?: string
  }
  workflowId?: string
  options?: {
    forecastDays?: number
    aqForecastDays?: number
    enableAnomalyDetection?: boolean
  }
  riskRules?: {
    pm10Weight?: number
  }
}
