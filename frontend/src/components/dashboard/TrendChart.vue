<script lang="ts">
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])
</script>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, shallowRef, useTemplateRef, watch } from 'vue'
import { init, type ComposeOption, type EChartsType } from 'echarts/core'

import type {
  GridComponentOption,
  LegendComponentOption,
  LineSeriesOption,
  TooltipComponentOption,
  XAXisComponentOption,
  YAXisComponentOption,
} from 'echarts'

import type { TrendSeries } from '../../types/dashboard'

type TrendChartOption = ComposeOption<
  | LineSeriesOption
  | GridComponentOption
  | LegendComponentOption
  | TooltipComponentOption
  | XAXisComponentOption
  | YAXisComponentOption
>

const props = withDefaults(
  defineProps<{
    title: string
    series: TrendSeries[]
    chartReady?: boolean
  }>(),
  {
    chartReady: true,
  },
)

const chartRef = useTemplateRef<HTMLDivElement>('chartRef')
const chartInstance = shallowRef<EChartsType | null>(null)
const isChartReady = computed(() => props.chartReady !== false)
const canUseWindow = typeof window !== 'undefined'

const renderableSeries = computed(() =>
  props.series.filter((item) => item.data.some((point) => point.value !== null)),
)

function formatAxisLabel(timestamp: string) {
  const match = timestamp.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2})/)

  if (match) {
    return `${match[2]}/${match[3]} ${match[4]}`
  }

  return timestamp
}

const chartOption = computed<TrendChartOption>(() => {
  const xAxisLabels = renderableSeries.value[0]?.data.map((point) => formatAxisLabel(point.time)) ?? []

  return {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      top: 0,
    },
    grid: {
      left: 16,
      right: 16,
      top: 48,
      bottom: 32,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisLabels,
      axisLabel: {
        hideOverlap: true,
        formatter: (value: string) => value.replace(' ', '\n'),
      },
    },
    yAxis: {
      type: 'value',
    },
    series: renderableSeries.value.map((item) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: item.data.map((point) => point.value),
    })),
  }
})

function renderChart() {
  if (!isChartReady.value || !chartRef.value || !renderableSeries.value.length) {
    return
  }

  if (!chartInstance.value) {
    chartInstance.value = init(chartRef.value)
  }

  chartInstance.value.setOption(chartOption.value)
}

function handleResize() {
  chartInstance.value?.resize()
}

watch([chartOption, isChartReady], () => {
  renderChart()
})

onMounted(() => {
  renderChart()
  if (canUseWindow) {
    window.addEventListener('resize', handleResize)
  }
})

onBeforeUnmount(() => {
  if (canUseWindow) {
    window.removeEventListener('resize', handleResize)
  }
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<template>
  <ElCard shadow="hover" class="trend-chart">
    <template #header>
      <div class="trend-chart__header">
        <span>{{ title }}</span>
        <ElTag type="info" effect="plain">{{ renderableSeries.length }} 条曲线</ElTag>
      </div>
    </template>

    <div v-if="!isChartReady" class="trend-chart__loading-state">
      <ElSkeleton :rows="6" animated />
      <p class="trend-chart__loading">图表加载中...</p>
    </div>
    <div v-else-if="renderableSeries.length" ref="chartRef" class="trend-chart__canvas" />
    <ElEmpty v-else description="当前没有可展示的趋势数据" :image-size="72" />
  </ElCard>
</template>

<style scoped>
.trend-chart__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.trend-chart__canvas {
  width: 100%;
  height: 320px;
}

.trend-chart__loading-state {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-chart__loading {
  margin: 0;
  color: var(--el-text-color-secondary);
}
</style>
