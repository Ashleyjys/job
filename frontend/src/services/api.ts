import type { DashboardQueryPayload, DashboardViewModel, LocationSearchResult } from '../types/dashboard'

const DEFAULT_API_BASE_URL = '/api'

export function createApiUrl(baseUrl: string, path: string): string {
  if (/^https?:\/\//.test(baseUrl)) {
    return `${baseUrl.replace(/\/$/, '')}${path}`
  }

  return `${baseUrl.replace(/\/$/, '')}${path}`
}

function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
}

function buildApiPath(baseUrl: string, resourcePath: string): string {
  return baseUrl === '/api' ? `/v1${resourcePath}` : `/api/v1${resourcePath}`
}

export async function queryDashboard(payload: DashboardQueryPayload): Promise<DashboardViewModel> {
  const baseUrl = getApiBaseUrl()
  const path = buildApiPath(baseUrl, '/dashboard/query')
  const response = await fetch(createApiUrl(baseUrl, path), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`Dashboard query failed with status ${response.status}`)
  }

  return response.json() as Promise<DashboardViewModel>
}

export async function searchLocations(query: string, count = 8): Promise<LocationSearchResult[]> {
  const baseUrl = getApiBaseUrl()
  const params = new URLSearchParams({
    q: query,
    count: String(count),
  })
  const path = `${buildApiPath(baseUrl, '/locations/search')}?${params.toString()}`
  const response = await fetch(createApiUrl(baseUrl, path))

  if (!response.ok) {
    throw new Error(`Location search failed with status ${response.status}`)
  }

  return response.json() as Promise<LocationSearchResult[]>
}
