<script setup lang="ts">
import { computed } from 'vue'

import type { DataSourceStatus } from '../../types/dashboard'

const props = defineProps<{
  notices: string[]
  sourceStatus: DataSourceStatus
  anomalyMessages: string[]
  generatedAt?: string
}>()

const sourceValues = computed(() => Object.values(props.sourceStatus))
const okCount = computed(() => sourceValues.value.filter((value) => value === 'ok').length)
const degradedCount = computed(() => sourceValues.value.filter((value) => value === 'degraded').length)
const failedCount = computed(() => sourceValues.value.filter((value) => value === 'failed').length)

const pipelineHeadline = computed(() => {
  if (failedCount.value > 0) {
    return '链路存在阻塞，建议优先处理故障节点'
  }

  if (degradedCount.value > 0) {
    return '链路存在波动，请关注数据时效与结果稳定性'
  }

  return '当前链路运行稳定'
})

const pipelineTagType = computed(() => {
  if (failedCount.value > 0) {
    return 'danger'
  }

  if (degradedCount.value > 0) {
    return 'warning'
  }

  return 'success'
})

const pipelineAlertType = computed(() => {
  if (failedCount.value > 0) {
    return 'error'
  }

  if (degradedCount.value > 0) {
    return 'warning'
  }

  return 'success'
})

const overviewCards = computed(() => [
  {
    title: '链路总览',
    value: '3 个关键环节',
    caption: `${okCount.value} 个正常 / ${degradedCount.value} 个降级 / ${failedCount.value} 个故障`,
  },
  {
    title: '运行提示',
    value: `${props.notices.length} 条提示`,
    caption: props.notices.length ? '建议结合业务上下文继续跟进' : '暂无额外提示',
  },
  {
    title: '异常检测',
    value: `${props.anomalyMessages.length} 条异常`,
    caption: props.anomalyMessages.length ? '已捕捉到异常波动信号' : '当前未发现异常波动',
  },
])

const generatedTimeLabel = computed(() => {
  if (!props.generatedAt) {
    return ''
  }

  const match = props.generatedAt.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2})/)

  if (match) {
    return `${match[2]}/${match[3]} ${match[4]}`
  }

  return props.generatedAt
})
</script>

<template>
  <ElCard shadow="hover" class="status-panel">
    <template #header>
      <div class="status-panel__header">
        <div>
          <p class="status-panel__title">系统状态</p>
          <p class="status-panel__subtitle">围绕数据获取、分析处理与结果展示的运行快照</p>
        </div>
        <ElTag :type="pipelineTagType" effect="dark" round class="status-panel__header-tag">{{ pipelineHeadline }}</ElTag>
      </div>
    </template>

    <div class="status-panel__overview">
      <div v-for="item in overviewCards" :key="item.title" class="status-panel__overview-card">
        <p class="status-panel__overview-title">{{ item.title }}</p>
        <p class="status-panel__overview-value">{{ item.value }}</p>
        <p class="status-panel__overview-caption">{{ item.caption }}</p>
      </div>
    </div>

    <ElAlert
      :title="pipelineHeadline"
      :type="pipelineAlertType"
      :closable="false"
      show-icon
      class="status-panel__summary-alert"
    >
      <template #default>
        <span v-if="generatedTimeLabel">最近更新：{{ generatedTimeLabel }}</span>
        <span v-else>状态会随城市切换与刷新请求同步更新。</span>
      </template>
    </ElAlert>

    <section class="status-panel__section">
      <div class="status-panel__section-header">
        <span>运行提示</span>
        <ElTag type="info" effect="plain" class="status-panel__section-tag">{{ props.notices.length }} 条</ElTag>
      </div>

      <div v-if="props.notices.length" class="status-panel__alerts">
        <ElAlert
          v-for="notice in props.notices"
          :key="notice"
          :title="notice"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
      <p v-else class="status-panel__empty-copy">暂无额外提示</p>
    </section>

    <section class="status-panel__section">
      <div class="status-panel__section-header">
        <span>异常检测</span>
        <ElTag :type="props.anomalyMessages.length ? 'warning' : 'success'" effect="plain" class="status-panel__section-tag">
          {{ props.anomalyMessages.length }} 条
        </ElTag>
      </div>

      <div v-if="props.anomalyMessages.length" class="status-panel__alerts">
        <ElAlert
          v-for="message in props.anomalyMessages"
          :key="message"
          :title="message"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
      <p v-else class="status-panel__empty-copy">当前未发现异常波动</p>
    </section>
  </ElCard>
</template>

<style scoped>
.status-panel {
  height: 100%;
}

.status-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.status-panel__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.status-panel__subtitle {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.status-panel__overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.status-panel__overview-card {
  padding: 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-fill-color-blank);
  min-height: 140px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-panel__overview-title,
.status-panel__overview-caption,
.status-panel__empty-copy {
  margin: 0;
  color: var(--el-text-color-secondary);
}

.status-panel__overview-value {
  margin: 2px 0 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.status-panel__overview-caption,
.status-panel__empty-copy {
  line-height: 1.6;
}

.status-panel__overview-caption {
  margin-top: auto;
}

.status-panel__summary-alert,
.status-panel__section {
  margin-top: 16px;
}

.status-panel__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.status-panel__alerts {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.status-panel__header-tag,
.status-panel__section-tag {
  flex-shrink: 0;
  font-weight: 600;
}

@media (max-width: 900px) {
  .status-panel__overview {
    grid-template-columns: 1fr;
  }
}
</style>
