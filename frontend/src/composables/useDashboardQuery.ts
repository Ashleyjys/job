import { computed, shallowRef } from 'vue'

import { queryDashboard } from '../services/api'
import type { DashboardQueryFormValues, DashboardQueryPayload, DashboardViewModel } from '../types/dashboard'

export function useDashboardQuery() {
  const dashboard = shallowRef<DashboardViewModel | null>(null)
  const isLoading = shallowRef(false)
  const error = shallowRef<string | null>(null)

  const currentCity = computed(() => dashboard.value?.location.name ?? '成都')

  async function loadDashboard(query: DashboardQueryFormValues) {
    isLoading.value = true
    error.value = null

    const payload: DashboardQueryPayload = {
      city: query.city,
      options: {
        forecastDays: query.forecastDays,
        aqForecastDays: query.aqForecastDays,
        enableAnomalyDetection: query.enableAnomalyDetection,
      },
    }

    if (query.selectedLocation) {
      payload.location = {
        latitude: query.selectedLocation.latitude,
        longitude: query.selectedLocation.longitude,
        timezone: query.selectedLocation.timezone,
      }
    }

    if (query.pm10Weight !== null && query.pm10Weight !== undefined) {
      payload.riskRules = {
        pm10Weight: query.pm10Weight,
      }
    }

    try {
      dashboard.value = await queryDashboard(payload)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  return {
    dashboard,
    currentCity,
    isLoading,
    error,
    loadDashboard,
  }
}
