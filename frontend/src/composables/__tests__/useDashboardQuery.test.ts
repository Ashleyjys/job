import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useDashboardQuery } from '../useDashboardQuery'

vi.mock('../../services/api', () => ({
  queryDashboard: vi.fn().mockResolvedValue({
    traceId: 'trace-1',
    workflowRunId: 'workflow-1',
    location: {
      name: 'Beijing',
      latitude: 39.9,
      longitude: 116.4,
      timezone: 'Asia/Shanghai',
    },
    currentMetrics: [],
    weatherTrend: [],
    airQualityTrend: [],
    dailyForecast: [],
    risk: {
      riskScore: 12,
      riskLevel: 'low',
      primaryFactors: [],
      summary: 'ok',
      status: 'ok',
    },
    anomaly: {
      hasAnomaly: false,
      anomalyFlags: [],
      severity: 'none',
      messages: [],
      status: 'ok',
    },
    sourceStatus: {
      weather: 'ok',
      airQuality: 'ok',
      analysis: 'ok',
    },
    notices: [],
    generatedAt: '2026-06-07T00:00:00Z',
  }),
}))

import { queryDashboard } from '../../services/api'

describe('useDashboardQuery', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes the selected query parameters to the request layer', async () => {
    const { loadDashboard } = useDashboardQuery()

    await loadDashboard({
      city: 'Shanghai',
      forecastDays: 10,
      aqForecastDays: 6,
      enableAnomalyDetection: false,
    })

    expect(queryDashboard).toHaveBeenCalledWith({
      city: 'Shanghai',
      options: {
        forecastDays: 10,
        aqForecastDays: 6,
        enableAnomalyDetection: false,
      },
    })
  })

  it('passes the selected location coordinates when the user chooses a specific city candidate', async () => {
    const { loadDashboard } = useDashboardQuery()

    await loadDashboard({
      city: 'Chengdu',
      forecastDays: 3,
      aqForecastDays: 3,
      enableAnomalyDetection: true,
      selectedLocation: {
        name: 'Chengdu',
        country: 'China',
        admin1: 'Sichuan',
        latitude: 30.66667,
        longitude: 104.06667,
        timezone: 'Asia/Shanghai',
      },
    })

    expect(queryDashboard).toHaveBeenCalledWith({
      city: 'Chengdu',
      location: {
        latitude: 30.66667,
        longitude: 104.06667,
        timezone: 'Asia/Shanghai',
      },
      options: {
        forecastDays: 3,
        aqForecastDays: 3,
        enableAnomalyDetection: true,
      },
    })
  })

  it('passes pm10Weight only when the user explicitly configures it', async () => {
    const { loadDashboard } = useDashboardQuery()

    await loadDashboard({
      city: 'Beijing',
      forecastDays: 7,
      aqForecastDays: 5,
      enableAnomalyDetection: true,
      pm10Weight: 0.1,
    })

    expect(queryDashboard).toHaveBeenCalledWith({
      city: 'Beijing',
      options: {
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
      },
      riskRules: {
        pm10Weight: 0.1,
      },
    })
  })

  it('does not send pm10Weight when the optional field is left empty', async () => {
    const { loadDashboard } = useDashboardQuery()

    await loadDashboard({
      city: 'Beijing',
      forecastDays: 7,
      aqForecastDays: 5,
      enableAnomalyDetection: true,
      pm10Weight: null,
    })

    expect(queryDashboard).toHaveBeenCalledWith({
      city: 'Beijing',
      options: {
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
      },
    })
  })
})
