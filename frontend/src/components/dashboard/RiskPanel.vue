<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  riskScore: number | null
  riskLevel: string
  summary: string
  primaryFactors?: string[]
}>()

const factorLabelMap: Record<string, string> = {
  aqi: 'AQI 偏高',
  pm25: 'PM2.5 偏高',
  pm2_5: 'PM2.5 偏高',
  humidity: '湿度偏高',
  temperature: '高温暴露',
}

const normalizedFactors = computed(() => props.primaryFactors?.filter(Boolean) ?? [])
const formattedFactors = computed(() =>
  normalizedFactors.value.map((factor) => factorLabelMap[factor] ?? factor.toUpperCase()),
)

const badgeLabel = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return '高风险'
    case 'medium':
      return '中风险'
    case 'low':
      return '低风险'
    default:
      return '待确认'
  }
})

const riskHeadline = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return '当前城市空气风险较高'
    case 'medium':
      return '当前城市空气风险中等'
    case 'low':
      return '当前城市空气风险较低'
    default:
      return '当前城市空气风险待进一步确认'
  }
})

const tagType = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
      return 'success'
    default:
      return 'info'
  }
})

const alertType = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return 'error'
    case 'medium':
      return 'warning'
    case 'low':
      return 'success'
    default:
      return 'info'
  }
})

const factorCountLabel = computed(() => {
  return formattedFactors.value.length ? `${formattedFactors.value.length} 项` : '无重点项'
})

const adviceTagLabel = computed(() => {
  switch (props.riskLevel) {
    case 'high':
      return '立即防护'
    case 'medium':
      return '持续关注'
    case 'low':
      return '常规关注'
    default:
      return '继续观察'
  }
})

const overviewCards = computed(() => [
  {
    title: '风险评分',
    value: props.riskScore === null ? '--' : `${props.riskScore} 分`,
    caption: '综合天气、AQI 与异常检测',
  },
  {
    title: '风险等级',
    value: badgeLabel.value,
    caption: props.riskLevel === 'high' ? '建议立即采取防护' : '结合实时数据动态判断',
  },
  {
    title: '关键因子',
    value: normalizedFactors.value.length ? `${normalizedFactors.value.length} 项因子` : '暂无重点因子',
    caption: normalizedFactors.value.length ? '用于解释当前风险判断' : '当前暂无明显放大项',
  },
])

const adviceList = computed(() => {
  if (props.riskLevel === 'high') {
    return [
      '减少长时间户外活动',
      '敏感人群外出佩戴口罩',
      '优先选择空气较好的时段出行',
    ]
  }

  if (props.riskLevel === 'medium') {
    return [
      '控制户外停留时长',
      '持续关注 AQI 与异常提示',
    ]
  }

  if (props.riskLevel === 'low') {
    return [
      '正常安排日常出行',
      '保持基础防护习惯',
    ]
  }

  return ['继续观察实时数据变化']
})
</script>

<template>
  <ElCard shadow="hover" class="risk-panel">
    <template #header>
      <div class="risk-panel__header">
        <div>
          <p class="risk-panel__title">风险评分</p>
          <p class="risk-panel__subtitle">围绕 AQI、PM2.5 与异常检测结果形成的风险快照</p>
        </div>
        <ElTag :type="tagType" effect="dark" round class="risk-panel__header-tag">{{ badgeLabel }}</ElTag>
      </div>
    </template>

    <div class="risk-panel__overview">
      <div v-for="item in overviewCards" :key="item.title" class="risk-panel__overview-card">
        <p class="risk-panel__overview-title">{{ item.title }}</p>
        <p class="risk-panel__overview-value">{{ item.value }}</p>
        <p class="risk-panel__overview-caption">{{ item.caption }}</p>
      </div>
    </div>

    <ElAlert
      :title="riskHeadline"
      :type="alertType"
      :closable="false"
      show-icon
      class="risk-panel__summary-alert"
    >
      <template #default>
        <span>{{ props.summary }}</span>
      </template>
    </ElAlert>

    <section class="risk-panel__section">
      <div class="risk-panel__section-header">
        <span>关键因子</span>
        <ElTag type="info" effect="plain" class="risk-panel__section-tag">{{ factorCountLabel }}</ElTag>
      </div>

      <div v-if="normalizedFactors.length" class="risk-panel__factor-list">
        <ElTag v-for="factor in formattedFactors" :key="factor" type="warning" effect="light" round>
          {{ factor }}
        </ElTag>
      </div>
      <p v-else class="risk-panel__empty-copy">暂无重点因子</p>
    </section>

    <section class="risk-panel__section">
      <div class="risk-panel__section-header">
        <span>处置建议</span>
        <ElTag :type="tagType" effect="plain" class="risk-panel__section-tag">{{ adviceTagLabel }}</ElTag>
      </div>

      <div class="risk-panel__advice-list">
        <p v-for="advice in adviceList" :key="advice" class="risk-panel__advice-item">{{ advice }}</p>
      </div>
    </section>
  </ElCard>
</template>

<style scoped>
.risk-panel {
  height: 100%;
}

.risk-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.risk-panel__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.risk-panel__subtitle {
  margin: 6px 0 0;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.risk-panel__overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.risk-panel__overview-card {
  padding: 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-fill-color-blank);
  min-height: 140px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-panel__overview-title,
.risk-panel__overview-caption,
.risk-panel__empty-copy,
.risk-panel__advice-item {
  margin: 0;
  color: var(--el-text-color-secondary);
}

.risk-panel__overview-value {
  margin: 2px 0 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.risk-panel__overview-caption,
.risk-panel__empty-copy,
.risk-panel__advice-item {
  line-height: 1.6;
}

.risk-panel__overview-caption {
  margin-top: auto;
}

.risk-panel__summary-alert,
.risk-panel__section {
  margin-top: 16px;
}

.risk-panel__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.risk-panel__factor-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.risk-panel__advice-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.risk-panel__header-tag,
.risk-panel__section-tag {
  flex-shrink: 0;
  min-width: 72px;
  font-weight: 600;
  justify-content: center;
}

@media (max-width: 900px) {
  .risk-panel__overview {
    grid-template-columns: 1fr;
  }
}
</style>
