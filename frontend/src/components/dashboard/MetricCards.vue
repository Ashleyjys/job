<script setup lang="ts">
import { computed } from 'vue'

import type { MetricCardItem } from '../../types/dashboard'

const props = defineProps<{
  metrics: MetricCardItem[]
}>()

const cards = computed(() => props.metrics)
const metricLabelMap: Record<string, string> = {
  Temperature: '温度',
  Humidity: '湿度',
  AQI: '空气质量指数',
  'PM2.5': '细颗粒物',
}

function resolveDisplayUnit(metric: MetricCardItem) {
  if (!metric.unit) {
    return undefined
  }

  if (metric.key === 'temperature' || metric.label === 'Temperature') {
    return '°C'
  }

  return metric.unit
}

function resolveDisplayValue(metric: MetricCardItem) {
  const value = metric.value ?? '--'
  const unit = resolveDisplayUnit(metric)

  return unit ? `${value} ${unit}` : String(value)
}

function resolveTagType(status?: MetricCardItem['status']) {
  switch (status) {
    case 'warning':
      return 'warning'
    case 'danger':
      return 'danger'
    case 'normal':
      return 'success'
    default:
      return 'info'
  }
}

function resolveDisplayLabel(metric: MetricCardItem) {
  const chineseLabel = metricLabelMap[metric.label]

  if (!chineseLabel) {
    return metric.label
  }

  return `${metric.label} / ${chineseLabel}`
}

function resolveCardModifier(status?: MetricCardItem['status']) {
  switch (status) {
    case 'warning':
      return 'metric-card--warning'
    case 'danger':
      return 'metric-card--danger'
    case 'normal':
      return 'metric-card--normal'
    default:
      return 'metric-card--neutral'
  }
}

function resolveTrendMarker(direction?: MetricCardItem['trendDirection']) {
  switch (direction) {
    case 'up':
      return '↗'
    case 'down':
      return '↘'
    case 'flat':
      return '→'
    default:
      return '·'
  }
}

function resolveTrendClass(direction?: MetricCardItem['trendDirection']) {
  switch (direction) {
    case 'up':
      return 'metric-card__trend--up'
    case 'down':
      return 'metric-card__trend--down'
    case 'flat':
      return 'metric-card__trend--flat'
    default:
      return 'metric-card__trend--unknown'
  }
}
</script>

<template>
  <ElRow :gutter="16" class="metric-grid">
    <ElCol v-for="metric in cards" :key="metric.key" :xs="24" :sm="12" :lg="6">
      <ElCard shadow="hover" :class="['metric-card', resolveCardModifier(metric.status)]">
        <template #header>
          <div class="metric-card__header">
            <span>{{ resolveDisplayLabel(metric) }}</span>
            <ElTag :type="resolveTagType(metric.status)" effect="dark" round>
              {{ metric.status || 'unknown' }}
            </ElTag>
          </div>
        </template>

        <div class="metric-card__value-row">
          <div class="metric-card__value">
            {{ resolveDisplayValue(metric) }}
          </div>
        </div>

        <div v-if="metric.trendSummary || metric.trendBadge || metric.insight" class="metric-card__meta">
          <ElTag
            v-if="metric.trendBadge"
            :type="resolveTagType(metric.status)"
            effect="light"
            round
            class="metric-card__badge"
          >
            {{ metric.trendBadge }}
          </ElTag>

          <p v-if="metric.trendSummary" :class="['metric-card__trend', resolveTrendClass(metric.trendDirection)]">
            <span class="metric-card__trend-marker">{{ resolveTrendMarker(metric.trendDirection) }}</span>
            <span>{{ metric.trendSummary }}</span>
          </p>

          <p v-if="metric.insight" class="metric-card__insight">{{ metric.insight }}</p>
        </div>
      </ElCard>
    </ElCol>
  </ElRow>
</template>

<style scoped>
.metric-grid {
  margin-top: 0;
}

.metric-card {
  margin-bottom: 16px;
  border: 1px solid transparent;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-card--neutral {
  border-color: var(--el-border-color-light);
}

.metric-card--normal {
  border-color: color-mix(in srgb, var(--el-color-success) 35%, white);
}

.metric-card--warning {
  border-color: color-mix(in srgb, var(--el-color-warning) 45%, white);
  box-shadow: 0 12px 24px rgba(230, 162, 60, 0.12);
}

.metric-card--danger {
  border-color: color-mix(in srgb, var(--el-color-danger) 48%, white);
  box-shadow: 0 14px 28px rgba(245, 108, 108, 0.14);
}

.metric-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
  line-height: 1.4;
}

.metric-card__value-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.metric-card__value {
  margin-bottom: 12px;
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1.2;
}

.metric-card__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.metric-card__badge {
  font-weight: 600;
}

.metric-card__trend {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
}

.metric-card__trend-marker {
  font-size: 1rem;
}

.metric-card__insight {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.metric-card__trend--up {
  color: var(--el-color-danger);
}

.metric-card__trend--down {
  color: var(--el-color-success);
}

.metric-card__trend--flat,
.metric-card__trend--unknown {
  color: var(--el-text-color-secondary);
}
</style>
