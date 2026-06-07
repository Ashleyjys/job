// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MetricCards from '../MetricCards.vue'

describe('MetricCards', () => {
  it('renders bilingual metric labels, corrected temperature unit, and trend summaries', () => {
    const wrapper = mount(MetricCards, {
      props: {
        metrics: [
          {
            key: 'temperature',
            label: 'Temperature',
            value: 30,
            unit: 'C',
            status: 'normal',
            trendDirection: 'up',
            trendBadge: '环比上升',
            trendSummary: '较上一时段上升 2 °C',
            insight: '体感偏热，注意补水',
          },
          {
            key: 'aqi',
            label: 'AQI',
            value: 118,
            unit: 'AQI',
            status: 'warning',
            trendDirection: 'down',
            trendBadge: '环比下降',
            trendSummary: '较上一时段下降 5 AQI',
            insight: '空气质量回落，仍需关注',
          },
        ],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('Temperature')
    expect(wrapper.text()).toContain('温度')
    expect(wrapper.text()).toContain('AQI')
    expect(wrapper.text()).toContain('空气质量指数')
    expect(wrapper.text()).toContain('30')
    expect(wrapper.text()).toContain('30 °C')
    expect(wrapper.text()).not.toContain('30 C')
    expect(wrapper.text()).toContain('118 AQI')
    expect(wrapper.text()).toContain('环比上升')
    expect(wrapper.text()).toContain('体感偏热，注意补水')
    expect(wrapper.text()).toContain('较上一时段上升 2 °C')
    expect(wrapper.text()).toContain('环比下降')
    expect(wrapper.text()).toContain('空气质量回落，仍需关注')
    expect(wrapper.text()).toContain('较上一时段下降 5 AQI')
  })

  it('renders Element Plus card and tag classes', () => {
    const wrapper = mount(MetricCards, {
      props: {
        metrics: [{ key: 'aqi', label: 'AQI', value: 118, unit: 'AQI', status: 'warning' }],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.find('.el-card').exists()).toBe(true)
    expect(wrapper.find('.el-tag').exists()).toBe(true)
  })

  it('applies stronger visual emphasis classes for warning and danger states', () => {
    const wrapper = mount(MetricCards, {
      props: {
        metrics: [
          { key: 'aqi', label: 'AQI', value: 118, unit: 'AQI', status: 'warning' },
          { key: 'pm25', label: 'PM2.5', value: 160, unit: 'ug/m3', status: 'danger' },
        ],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    const cards = wrapper.findAll('.metric-card')

    expect(cards[0]?.classes()).toContain('metric-card--warning')
    expect(cards[1]?.classes()).toContain('metric-card--danger')
  })
})
