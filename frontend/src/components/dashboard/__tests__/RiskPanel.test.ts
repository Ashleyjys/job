// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RiskPanel from '../RiskPanel.vue'

describe('RiskPanel', () => {
  it('renders concise product-style factor and advice tags without misusing the score in section headers', () => {
    const wrapper = mount(RiskPanel, {
      props: {
        riskScore: 85,
        riskLevel: 'high',
        summary: 'AQI 与 PM2.5 偏高，建议减少长时间户外活动并关注后续变化。',
        primaryFactors: ['aqi', 'pm25'],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('风险评分')
    expect(wrapper.text()).toContain('高风险')
    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('风险等级')
    expect(wrapper.text()).toContain('关键因子')
    expect(wrapper.text()).toContain('2 项因子')
    expect(wrapper.text()).toContain('处置建议')

    const sectionHeaderTags = wrapper.findAll('.risk-panel__section-header .el-tag').map((tag) => tag.text().trim())
    expect(sectionHeaderTags).toEqual(['2 项', '立即防护'])
    expect(sectionHeaderTags).not.toContain('85')
    expect(sectionHeaderTags).not.toContain('高风险')

    expect(wrapper.text()).toContain('AQI 偏高')
    expect(wrapper.text()).toContain('PM2.5 偏高')
    expect(wrapper.text()).toContain('减少长时间户外活动')
    expect(wrapper.text()).toContain('敏感人群外出佩戴口罩')
  })

  it('renders a stable low-risk message when the score is mild', () => {
    const wrapper = mount(RiskPanel, {
      props: {
        riskScore: 22,
        riskLevel: 'low',
        summary: '整体空气风险较低，可正常安排日常出行。',
        primaryFactors: [],
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('低风险')
    expect(wrapper.text()).toContain('当前城市空气风险较低')
    expect(wrapper.text()).toContain('暂无重点因子')
  })
})
