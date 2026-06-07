// @vitest-environment jsdom

import ElementPlus from 'element-plus'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CitySelector from '../CitySelector.vue'

const cityOptions = [
  {
    label: 'Chengdu / Sichuan / China',
    value: 'Chengdu',
    location: {
      name: 'Chengdu',
      country: 'China',
      admin1: 'Sichuan',
      latitude: 30.66667,
      longitude: 104.06667,
      timezone: 'Asia/Shanghai',
    },
  },
  {
    label: 'New York / New York / United States',
    value: 'New York',
    location: {
      name: 'New York',
      country: 'United States',
      admin1: 'New York',
      latitude: 40.71427,
      longitude: -74.00597,
      timezone: 'America/New_York',
    },
  },
]

describe('CitySelector', () => {
  it('uses top-aligned labels so the compact controls stay visually aligned', () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: 'Chengdu',
        selectedLocation: null,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        pm10Weight: null,
        cityOptions,
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    const form = wrapper.findComponent({ name: 'ElForm' })

    expect(form.props('labelPosition')).toBe('top')
  })

  it('does not offer a 7-day option for air quality forecasts', () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: 'Chengdu',
        selectedLocation: null,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        cityOptions,
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    const labels = wrapper.findAllComponents({ name: 'ElOption' }).map((item) => item.props('label'))

    expect(labels.filter((label) => label === '7 天')).toHaveLength(1)
  })

  it('renders the query parameter controls and supplied city options', () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: 'Chengdu',
        selectedLocation: null,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        pm10Weight: null,
        cityOptions,
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.text()).toContain('天气预测天数')
    expect(wrapper.text()).toContain('空气质量预测天数')
    expect(wrapper.text()).toContain('异常检测')
    expect(wrapper.text()).toContain('PM10 权重')

    const options = wrapper.findAllComponents({ name: 'ElOption' })
    expect(options.map((item) => item.props('label'))).toEqual(
      expect.arrayContaining(['Chengdu / Sichuan / China', 'New York / New York / United States']),
    )
  })

  it('emits remote search queries when the user types a city keyword', async () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: '',
        selectedLocation: null,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        pm10Weight: null,
        cityOptions: [],
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await (wrapper.vm as unknown as { handleCitySearch: (query: string) => void }).handleCitySearch('cheng')

    expect(wrapper.emitted('searchCity')).toEqual([['cheng']])
  })

  it('updates the selected location when the user chooses a matched city option', async () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: 'Chengdu',
        selectedLocation: null,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        pm10Weight: null,
        cityOptions,
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await (wrapper.vm as unknown as { handleCityChange: (value: string) => void }).handleCityChange('Chengdu')

    expect(wrapper.emitted('update:selectedLocation')).toEqual([[cityOptions[0].location]])
  })

  it('submits the selected city candidate together with the current query options', async () => {
    const wrapper = mount(CitySelector, {
      props: {
        modelValue: 'Chengdu',
        selectedLocation: cityOptions[0].location,
        forecastDays: 7,
        aqForecastDays: 5,
        enableAnomalyDetection: true,
        pm10Weight: 0.1,
        cityOptions,
        citySearchLoading: false,
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('submit')).toEqual([
      [
        {
          city: 'Chengdu',
          forecastDays: 7,
          aqForecastDays: 5,
          enableAnomalyDetection: true,
          pm10Weight: 0.1,
          selectedLocation: cityOptions[0].location,
        },
      ],
    ])
  })
})
