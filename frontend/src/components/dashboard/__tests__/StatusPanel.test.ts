// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import StatusPanel from '../StatusPanel.vue'

describe('StatusPanel', () => {
  it('renders a condensed operational summary without repeating the chain overview detail section', () => {
    const wrapper = mount(StatusPanel, {
      props: {
        notices: ['天气数据源响应变慢，请关注同步延迟'],
        sourceStatus: {
          weather: 'ok',
          airQuality: 'degraded',
          analysis: 'failed',
        },
        anomalyMessages: ['检测到 AQI 突增，请尽快核查'],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('系统状态')
    expect(wrapper.text()).toContain('链路总览')
    expect(wrapper.text()).toContain('3 个关键环节')
    expect(wrapper.text()).toContain('运行提示')
    expect(wrapper.text()).toContain('异常检测')
    expect(wrapper.text()).toContain('1 条提示')
    expect(wrapper.text()).toContain('1 条异常')
    expect(wrapper.text()).toContain('1 个正常 / 1 个降级 / 1 个故障')
    expect(wrapper.text().match(/链路总览/g)).toHaveLength(1)
    expect(wrapper.find('.status-panel__source-grid').exists()).toBe(false)
    expect(wrapper.findAll('.status-panel__section')).toHaveLength(2)
  })

  it('renders a stable summary when the pipeline is healthy', () => {
    const wrapper = mount(StatusPanel, {
      props: {
        notices: [],
        sourceStatus: {
          weather: 'ok',
          airQuality: 'ok',
          analysis: 'ok',
        },
        anomalyMessages: [],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('当前链路运行稳定')
    expect(wrapper.text()).toContain('暂无额外提示')
  })
})
