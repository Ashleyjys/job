import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createApiUrl, searchLocations } from '../api'

describe('createApiUrl', () => {
  it('builds dashboard query url from base url and path', () => {
    expect(createApiUrl('http://localhost:8000', '/api/v1/dashboard/query')).toBe(
      'http://localhost:8000/api/v1/dashboard/query',
    )
  })

  it('builds relative proxy url from local api base and path', () => {
    expect(createApiUrl('/api', '/v1/dashboard/query')).toBe('/api/v1/dashboard/query')
  })
})

describe('searchLocations', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [
          {
            name: 'Chengdu',
            country: 'China',
            admin1: 'Sichuan',
            latitude: 30.66667,
            longitude: 104.06667,
            timezone: 'Asia/Shanghai',
          },
        ],
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('requests remote city suggestions from the local proxy path', async () => {
    await searchLocations('cheng', 8)

    expect(fetch).toHaveBeenCalledWith('/api/v1/locations/search?q=cheng&count=8')
  })
})
