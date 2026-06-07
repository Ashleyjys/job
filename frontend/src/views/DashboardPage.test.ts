// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { flushPromises, mount } from '@vue/test-utils'
import { computed, shallowRef } from 'vue'
import { describe, expect, it, vi } from 'vitest'

const { searchLocationsMock } = vi.hoisted(() => ({
  searchLocationsMock: vi.fn(),
}))

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  })),
}))

vi.mock('../services/api', () => ({
  searchLocations: searchLocationsMock,
}))

import DashboardPage from './DashboardPage.vue'

const dashboardState = shallowRef({
  traceId: 'trace-1',
  workflowRunId: 'workflow-1',
  location: {
    name: 'Beijing',
    latitude: 39.9,
    longitude: 116.4,
    timezone: 'Asia/Shanghai',
  },
  currentMetrics: [
    {
      key: 'temperature',
      label: 'Temperature',
      value: 30,
      unit: 'C',
      status: 'normal',
    },
    {
      key: 'aqi',
      label: 'AQI',
      value: 80,
      unit: 'AQI',
      status: 'warning',
    },
  ],
  weatherTrend: [
    {
      name: 'Temperature',
      unit: 'C',
      data: [
        { time: '2026-06-07T13:00:00Z', value: 28 },
        { time: '2026-06-07T14:00:00Z', value: 30 },
      ],
    },
  ],
  airQualityTrend: [
    {
      name: 'AQI',
      unit: 'AQI',
      data: [
        { time: '2026-06-07T13:00:00Z', value: 85 },
        { time: '2026-06-07T14:00:00Z', value: 80 },
      ],
    },
  ],
  dailyForecast: [],
  risk: {
    riskScore: 20,
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
})

const isLoadingState = shallowRef(false)
const errorState = shallowRef<string | null>(null)
const loadDashboardMock = vi.fn()

vi.mock('../composables/useDashboardQuery', () => ({
  useDashboardQuery: () => ({
    dashboard: dashboardState,
    currentCity: computed(() => dashboardState.value?.location.name ?? 'Beijing'),
    isLoading: isLoadingState,
    error: errorState,
    loadDashboard: loadDashboardMock,
  }),
}))

describe('DashboardPage', () => {
  it('seeds the selector with Chengdu and marks the preset options as hot cities', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    const selector = wrapper.findComponent({ name: 'CitySelector' })
    const options = selector.props('cityOptions') as Array<{ value: string; badge?: string }>

    expect(selector.props('modelValue')).toBe('成都')
    expect(options[0]?.value).toBe('成都')
    expect(options.every((item) => item.badge === '热门搜索城市')).toBe(true)

    wrapper.unmount()
  })

  it('renders a decorative full-page backdrop behind the dashboard content', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    const backdrop = wrapper.find('.page-shell__backdrop')
    expect(backdrop.exists()).toBe(true)
    expect(backdrop.attributes('aria-hidden')).toBe('true')

    wrapper.unmount()
  })

  it('renders the dashboard hero copy', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('城市空气质量 / 天气联动分析看板')
    expect(wrapper.text()).toContain('Air Quality / Weather Linked Analysis Dashboard')
    expect(wrapper.text()).toContain('以城市为入口，串联天气、AQI、风险评分与异常检测平台')

    wrapper.unmount()
  })

  it('renders async chart loading placeholders with section labels', () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('天气趋势')
    expect(wrapper.text()).toContain('空气质量趋势')
    expect(wrapper.text()).toContain('趋势图加载中')

    wrapper.unmount()
  })

  it('renders localized trend section titles after async charts resolve', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('天气趋势')
    expect(wrapper.text()).toContain('空气质量趋势')

    wrapper.unmount()
  })

  it('renders the updated future weather panel title', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('未来天气预测')

    wrapper.unmount()
  })

  it('renders derived metric trend summaries from trend series', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('环比上升')
    expect(wrapper.text()).toContain('较上一时段上升 2 °C')
    expect(wrapper.text()).toContain('体感偏热，注意补水')
    expect(wrapper.text()).toContain('环比下降')
    expect(wrapper.text()).toContain('较上一时段下降 5 AQI')
    expect(wrapper.text()).toContain('空气质量回落，仍需关注')

    wrapper.unmount()
  })

  it('renders current metric labels', async () => {
    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Temperature')
    expect(wrapper.text()).toContain('温度')
    expect(wrapper.text()).toContain('30 °C')

    wrapper.unmount()
  })

  it('keeps the current dashboard content visible while a refresh is loading', async () => {
    isLoadingState.value = true

    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Temperature')
    expect(wrapper.find('.dashboard-loading-skeleton').exists()).toBe(false)

    isLoadingState.value = false
    wrapper.unmount()
  })

  it('shows an empty-result hint when city search returns no candidates', async () => {
    searchLocationsMock.mockResolvedValueOnce([])

    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    const selector = wrapper.findComponent({ name: 'CitySelector' })
    await (selector.vm as unknown as { handleCitySearch: (query: string) => void }).handleCitySearch('Atlantis')
    await flushPromises()

    expect(wrapper.text()).toContain('未找到匹配城市')
    expect(wrapper.text()).toContain('请尝试更完整的城市名称')
    expect(selector.props('cityOptions')).toEqual([])

    wrapper.unmount()
  })

  it('falls back to hot cities and shows a warning when city search fails', async () => {
    searchLocationsMock.mockRejectedValueOnce(new Error('network error'))

    const wrapper = mount(DashboardPage, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    const selector = wrapper.findComponent({ name: 'CitySelector' })
    await (selector.vm as unknown as { handleCitySearch: (query: string) => void }).handleCitySearch('Cheng')
    await flushPromises()

    expect(wrapper.text()).toContain('城市搜索暂时不可用')
    expect(wrapper.text()).toContain('已切换回热门城市')
    expect((selector.props('cityOptions') as Array<{ value: string }>).map((item) => item.value)).toEqual([
      '成都',
      '北京',
      '上海',
      '广州',
      '深圳',
      '杭州',
      '武汉',
      '西安',
    ])

    wrapper.unmount()
  })
})
