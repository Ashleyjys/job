// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { mount } from '@vue/test-utils'
import type { Component } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const echartsModules = vi.hoisted(() => ({
  lineChart: Symbol('LineChart'),
  gridComponent: Symbol('GridComponent'),
  legendComponent: Symbol('LegendComponent'),
  tooltipComponent: Symbol('TooltipComponent'),
  canvasRenderer: Symbol('CanvasRenderer'),
}))

const echartsSpies = vi.hoisted(() => ({
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  init: vi.fn(),
  use: vi.fn(),
}))

echartsSpies.init.mockImplementation(() => ({
  setOption: echartsSpies.setOption,
  resize: echartsSpies.resize,
  dispose: echartsSpies.dispose,
}))

vi.mock('echarts/core', () => ({
  init: echartsSpies.init,
  use: echartsSpies.use,
}))

vi.mock('echarts/charts', () => ({
  LineChart: echartsModules.lineChart,
}))

vi.mock('echarts/components', () => ({
  GridComponent: echartsModules.gridComponent,
  LegendComponent: echartsModules.legendComponent,
  TooltipComponent: echartsModules.tooltipComponent,
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: echartsModules.canvasRenderer,
}))

let TrendChart: Component

async function loadTrendChart() {
  vi.resetModules()
  echartsSpies.use.mockClear()
  echartsSpies.init.mockClear()
  echartsSpies.setOption.mockClear()
  echartsSpies.resize.mockClear()
  echartsSpies.dispose.mockClear()

  TrendChart = (await import('../TrendChart.vue')).default
}

function mountTrendChart(props: Record<string, unknown>) {
  return mount(TrendChart, {
    props,
    global: {
      plugins: [ElementPlus],
    },
  })
}

describe('TrendChart', () => {
  beforeEach(async () => {
    await loadTrendChart()
  })

  it('registers only the required echarts modules', () => {
    expect(echartsSpies.use).toHaveBeenCalledTimes(1)
    expect(echartsSpies.use).toHaveBeenCalledWith([
      echartsModules.lineChart,
      echartsModules.gridComponent,
      echartsModules.legendComponent,
      echartsModules.tooltipComponent,
      echartsModules.canvasRenderer,
    ])
  })

  it('renders a loading placeholder before the chart module becomes ready', () => {
    const wrapper = mountTrendChart({
      title: '天气趋势',
      series: [
        {
          name: 'Temperature',
          unit: 'C',
          data: [{ time: '2026-06-07T14:00:00Z', value: 30 }],
        },
      ],
      chartReady: false,
    })

    expect(wrapper.text()).toContain('图表加载中...')
    expect(wrapper.find('.trend-chart__canvas').exists()).toBe(false)
  })

  it('renders chart title and configures richer x-axis labels when series data exists', async () => {
    const wrapper = mountTrendChart({
      title: '天气趋势',
      series: [
        {
          name: 'Temperature',
          unit: 'C',
          data: [
            { time: '2026-06-07T14:00:00Z', value: 30 },
            { time: '2026-06-08T02:00:00Z', value: 31 },
          ],
        },
      ],
      chartReady: true,
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('天气趋势')
    expect(wrapper.find('.trend-chart__canvas').exists()).toBe(true)
    expect(echartsSpies.init).toHaveBeenCalledTimes(1)
    expect(echartsSpies.setOption).toHaveBeenCalledTimes(1)
    expect(echartsSpies.setOption.mock.calls[0]?.[0]).toMatchObject({
      xAxis: {
        data: ['06/07 14:00', '06/08 02:00'],
      },
    })
  })

  it('treats chartReady as ready when the prop is omitted', async () => {
    const wrapper = mountTrendChart({
      title: '天气趋势',
      series: [
        {
          name: 'Temperature',
          unit: 'C',
          data: [{ time: '2026-06-07T14:00:00Z', value: 30 }],
        },
      ],
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.find('.trend-chart__canvas').exists()).toBe(true)
    expect(echartsSpies.init).toHaveBeenCalledTimes(1)
  })

  it('renders empty state when no renderable trend series exist', () => {
    const wrapper = mountTrendChart({
      title: '空气质量趋势',
      series: [],
      chartReady: true,
    })

    expect(wrapper.text()).toContain('空气质量趋势')
    expect(wrapper.text()).toContain('当前没有可展示的趋势数据')
    expect(wrapper.find('.trend-chart__canvas').exists()).toBe(false)
  })
})
