<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, shallowRef } from 'vue'

import CitySelector from '../components/dashboard/CitySelector.vue'
import MetricCards from '../components/dashboard/MetricCards.vue'
import RiskPanel from '../components/dashboard/RiskPanel.vue'
import StatusPanel from '../components/dashboard/StatusPanel.vue'
import { useDashboardQuery } from '../composables/useDashboardQuery'
import { searchLocations } from '../services/api'
import type { CityOption, CitySearchStatus, DashboardQueryFormValues, LocationSearchResult, MetricCardItem } from '../types/dashboard'

const TrendChart = defineAsyncComponent({
  loader: () => import('../components/dashboard/TrendChart.vue'),
  delay: 200,
  timeout: 30000,
})

const HOT_CITY_BADGE = '热门搜索城市'

function createCityOption(location: LocationSearchResult, badge?: string): CityOption {
  const labelParts = [location.name, location.admin1, location.country].filter((part, index, items) => {
    if (!part) {
      return false
    }

    return items.indexOf(part) === index
  })

  return {
    label: labelParts.join(' / '),
    value: location.name,
    location,
    badge,
  }
}

function createHotCityOption(location: LocationSearchResult): CityOption {
  return createCityOption(location, HOT_CITY_BADGE)
}

const HOT_CITY_OPTIONS = [
  {
    name: '成都',
    country: '中国',
    admin1: '四川',
    latitude: 30.5728,
    longitude: 104.0668,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '北京',
    country: '中国',
    admin1: '北京',
    latitude: 39.9042,
    longitude: 116.4074,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '上海',
    country: '中国',
    admin1: '上海',
    latitude: 31.2304,
    longitude: 121.4737,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '广州',
    country: '中国',
    admin1: '广东',
    latitude: 23.1291,
    longitude: 113.2644,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '深圳',
    country: '中国',
    admin1: '广东',
    latitude: 22.5431,
    longitude: 114.0579,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '杭州',
    country: '中国',
    admin1: '浙江',
    latitude: 30.2741,
    longitude: 120.1551,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '武汉',
    country: '中国',
    admin1: '湖北',
    latitude: 30.5928,
    longitude: 114.3055,
    timezone: 'Asia/Shanghai',
  },
  {
    name: '西安',
    country: '中国',
    admin1: '陕西',
    latitude: 34.3416,
    longitude: 108.9398,
    timezone: 'Asia/Shanghai',
  },
].map(createHotCityOption)

const city = shallowRef('成都')
const selectedLocation = shallowRef<LocationSearchResult | null>(HOT_CITY_OPTIONS[0].location)
const cityOptions = shallowRef<CityOption[]>(HOT_CITY_OPTIONS)
const citySearchStatus = shallowRef<CitySearchStatus>('idle')
const citySearchLoading = shallowRef(false)
const forecastDays = shallowRef(7)
const aqForecastDays = shallowRef(5)
const enableAnomalyDetection = shallowRef(true)
const pm10Weight = shallowRef<number | null>(null)
let citySearchRequestId = 0

const { dashboard, currentCity, isLoading, error, loadDashboard } = useDashboardQuery()

const pageTitle = computed(() => `${currentCity.value} Air + Weather Overview`)
const showInitialSkeleton = computed(() => isLoading.value && !dashboard.value)
const showRefreshBanner = computed(() => isLoading.value && Boolean(dashboard.value))
const showErrorBanner = computed(() => Boolean(error.value) && Boolean(dashboard.value))
const citySearchMessage = computed(() => {
  switch (citySearchStatus.value) {
    case 'empty':
      return '未找到匹配城市，请尝试更完整的城市名称。'
    case 'error':
      return '城市搜索暂时不可用，已切换回热门城市。'
    default:
      return ''
  }
})

function resolveDisplayUnit(metric: MetricCardItem) {
  if (!metric.unit) {
    return ''
  }

  if (metric.key === 'temperature' || metric.label === 'Temperature') {
    return '°C'
  }

  return metric.unit
}

function resolveTrendBadge(delta: number) {
  if (delta > 0) {
    return '环比上升'
  }

  if (delta < 0) {
    return '环比下降'
  }

  return '环比持平'
}

function resolveMetricInsight(metric: MetricCardItem, delta: number) {
  switch (metric.key) {
    case 'temperature':
      if (delta > 0) {
        return '体感偏热，注意补水'
      }
      if (delta < 0) {
        return '温度回落，适合外出'
      }
      return '温度平稳，体感变化不大'
    case 'humidity':
      if (delta > 0) {
        return '湿度抬升，注意闷热感'
      }
      if (delta < 0) {
        return '空气更干爽，注意补水'
      }
      return '湿度稳定，体感较平稳'
    case 'aqi':
      if (delta > 0) {
        return '空气质量走弱，建议减少久待户外'
      }
      if (delta < 0) {
        return '空气质量回落，仍需关注'
      }
      return '空气质量持平，继续观察变化'
    case 'pm25':
      if (delta > 0) {
        return '细颗粒物上升，建议佩戴口罩'
      }
      if (delta < 0) {
        return '细颗粒物下降，呼吸压力减轻'
      }
      return '细颗粒物稳定，短时风险可控'
    default:
      return undefined
  }
}

const enhancedMetrics = computed(() => {
  const weatherTrendMap = new Map(dashboard.value?.weatherTrend.map((item) => [item.name, item]) ?? [])
  const airQualityTrendMap = new Map(dashboard.value?.airQualityTrend.map((item) => [item.name, item]) ?? [])

  return (dashboard.value?.currentMetrics ?? []).map((metric) => {
    const trendSource = weatherTrendMap.get(metric.label) ?? airQualityTrendMap.get(metric.label)
    const points = trendSource?.data.filter((item) => item.value !== null) ?? []

    if (points.length < 2) {
      return metric
    }

    const previous = points.at(-2)?.value
    const current = points.at(-1)?.value

    if (previous === null || previous === undefined || current === null || current === undefined) {
      return metric
    }

    const delta = Number((current - previous).toFixed(1))

    if (delta > 0) {
      return {
        ...metric,
        trendDirection: 'up' as const,
        trendBadge: resolveTrendBadge(delta),
        trendSummary: `较上一时段上升 ${delta} ${resolveDisplayUnit(metric)}`.trim(),
        insight: resolveMetricInsight(metric, delta),
      }
    }

    if (delta < 0) {
      return {
        ...metric,
        trendDirection: 'down' as const,
        trendBadge: resolveTrendBadge(delta),
        trendSummary: `较上一时段下降 ${Math.abs(delta)} ${resolveDisplayUnit(metric)}`.trim(),
        insight: resolveMetricInsight(metric, delta),
      }
    }

    return {
      ...metric,
      trendDirection: 'flat' as const,
      trendBadge: resolveTrendBadge(delta),
      trendSummary: '较上一时段持平',
      insight: resolveMetricInsight(metric, delta),
    }
  })
})

function getCurrentQuery(overrides?: Partial<DashboardQueryFormValues>): DashboardQueryFormValues {
  return {
    city: (overrides?.city ?? city.value).trim() || '成都',
    selectedLocation: overrides?.selectedLocation ?? selectedLocation.value,
    forecastDays: overrides?.forecastDays ?? forecastDays.value,
    aqForecastDays: overrides?.aqForecastDays ?? aqForecastDays.value,
    enableAnomalyDetection: overrides?.enableAnomalyDetection ?? enableAnomalyDetection.value,
    pm10Weight: overrides?.pm10Weight ?? pm10Weight.value,
  }
}

async function handleCitySearch(query: string) {
  const trimmed = query.trim()
  const requestId = ++citySearchRequestId

  if (!trimmed) {
    cityOptions.value = HOT_CITY_OPTIONS
    citySearchLoading.value = false
    citySearchStatus.value = 'idle'
    return
  }

  citySearchLoading.value = true
  citySearchStatus.value = 'loading'

  try {
    const results = await searchLocations(trimmed, 8)

    if (requestId !== citySearchRequestId) {
      return
    }

    cityOptions.value = results.map((location) => createCityOption(location))
    citySearchStatus.value = results.length > 0 ? 'idle' : 'empty'
  } catch {
    if (requestId !== citySearchRequestId) {
      return
    }

    cityOptions.value = HOT_CITY_OPTIONS
    citySearchStatus.value = 'error'
  } finally {
    if (requestId === citySearchRequestId) {
      citySearchLoading.value = false
    }
  }
}

async function refreshDashboard(nextQuery?: DashboardQueryFormValues) {
  const query = getCurrentQuery(nextQuery)
  await loadDashboard(query)
}

onMounted(async () => {
  await refreshDashboard(getCurrentQuery())
})
</script>

<template>
  <ElMain class="page-shell">
    <div class="page-shell__backdrop" aria-hidden="true" />

    <ElCard shadow="never" class="hero-card">
      <div class="hero-card__content">
        <div>
          <p class="hero-card__eyebrow">Air Quality / Weather Linked Analysis Dashboard</p>
          <h1 class="hero-card__title">城市空气质量 / 天气联动分析看板</h1>
          <p class="hero-card__subtitle">
            以城市为入口，串联天气、AQI、风险评分与异常检测平台
          </p>
        </div>
        <ElDescriptions :column="1" border class="hero-card__summary">
          <ElDescriptionsItem label="Current City">{{ currentCity }}</ElDescriptionsItem>
          <ElDescriptionsItem label="Overview">{{ pageTitle }}</ElDescriptionsItem>
        </ElDescriptions>
      </div>

      <CitySelector
        v-model="city"
        v-model:selected-location="selectedLocation"
        v-model:forecast-days="forecastDays"
        v-model:aq-forecast-days="aqForecastDays"
        v-model:enable-anomaly-detection="enableAnomalyDetection"
        v-model:pm10-weight="pm10Weight"
        :city-options="cityOptions"
        :city-search-status="citySearchStatus"
        :city-search-message="citySearchMessage"
        :city-search-loading="citySearchLoading"
        :submitting="isLoading"
        @search-city="handleCitySearch"
        @submit="refreshDashboard"
      />
    </ElCard>

    <ElAlert
      v-if="showRefreshBanner"
      title="看板数据更新中，将保留当前结果供你继续查看。"
      type="info"
      :closable="false"
      show-icon
      class="dashboard-block dashboard-refresh-banner"
    />
    <ElAlert
      v-if="showErrorBanner"
      :title="error!"
      type="warning"
      :closable="false"
      show-icon
      class="dashboard-block"
    />
    <ElSkeleton v-if="showInitialSkeleton" :rows="8" animated class="dashboard-block dashboard-loading-skeleton" />
    <ElAlert v-else-if="error && !dashboard" :title="error" type="error" :closable="false" show-icon class="dashboard-block" />

    <template v-else-if="dashboard">
      <section class="dashboard-block">
        <MetricCards :metrics="enhancedMetrics" />
      </section>

      <ElRow :gutter="16" class="dashboard-block">
        <ElCol :xs="24" :lg="14">
          <RiskPanel
            :risk-score="dashboard.risk.riskScore"
            :risk-level="dashboard.risk.riskLevel"
            :summary="dashboard.risk.summary"
            :primary-factors="dashboard.risk.primaryFactors"
          />
        </ElCol>
        <ElCol :xs="24" :lg="10">
          <StatusPanel
            :notices="dashboard.notices"
            :source-status="dashboard.sourceStatus"
            :anomaly-messages="dashboard.anomaly.messages"
            :generated-at="dashboard.generatedAt"
          />
        </ElCol>
      </ElRow>

      <ElRow :gutter="16" class="dashboard-block">
        <ElCol :xs="24" :xl="12">
          <Suspense>
            <TrendChart title="天气趋势" :series="dashboard.weatherTrend" />
            <template #fallback>
              <ElCard shadow="hover" class="dashboard-block trend-chart-fallback">
                <div class="trend-chart-fallback__header">
                  <span>天气趋势</span>
                  <ElTag type="info" effect="plain">加载中</ElTag>
                </div>
                <ElSkeleton :rows="6" animated />
                <p class="trend-chart__loading">趋势图加载中</p>
              </ElCard>
            </template>
          </Suspense>
        </ElCol>
        <ElCol :xs="24" :xl="12">
          <Suspense>
            <TrendChart title="空气质量趋势" :series="dashboard.airQualityTrend" />
            <template #fallback>
              <ElCard shadow="hover" class="dashboard-block trend-chart-fallback">
                <div class="trend-chart-fallback__header">
                  <span>空气质量趋势</span>
                  <ElTag type="info" effect="plain">加载中</ElTag>
                </div>
                <ElSkeleton :rows="6" animated />
                <p class="trend-chart__loading">趋势图加载中</p>
              </ElCard>
            </template>
          </Suspense>
        </ElCol>
      </ElRow>

      <ElCard shadow="hover" class="dashboard-block">
        <template #header>
          <div class="forecast-panel__header">
            <span>未来天气预测</span>
            <ElTag type="info" effect="plain">{{ dashboard.dailyForecast.length }} 天视图</ElTag>
          </div>
        </template>

        <ElRow :gutter="16">
          <ElCol
            v-for="item in dashboard.dailyForecast"
            :key="item.date"
            :xs="24"
            :sm="12"
            :lg="8"
            :xl="6"
          >
            <ElCard shadow="never" class="forecast-card">
              <p class="forecast-card__date">{{ item.date }}</p>
              <p class="forecast-card__temp">{{ item.maxTemperature }} / {{ item.minTemperature }} °C</p>
              <p class="forecast-card__wind">Wind {{ item.maxWindSpeed }} m/s</p>
            </ElCard>
          </ElCol>
        </ElRow>
      </ElCard>
    </template>
  </ElMain>
</template>

<style scoped>
.dashboard-refresh-banner {
  margin-bottom: 0;
}

.trend-chart-fallback {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-chart-fallback__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.trend-chart__loading {
  margin: 12px 0 0;
  color: var(--el-text-color-secondary);
}
</style>
