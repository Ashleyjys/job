<script setup lang="ts">
import { computed } from 'vue'

import type { CityOption, CitySearchStatus, DashboardQueryFormValues, LocationSearchResult } from '../../types/dashboard'

const city = defineModel<string>({ required: true })
const selectedLocation = defineModel<LocationSearchResult | null>('selectedLocation', { default: null })
const forecastDays = defineModel<number>('forecastDays', { required: true })
const aqForecastDays = defineModel<number>('aqForecastDays', { required: true })
const enableAnomalyDetection = defineModel<boolean>('enableAnomalyDetection', { required: true })
const pm10Weight = defineModel<number | null>('pm10Weight', { default: null })

const props = withDefaults(
  defineProps<{
    cityOptions?: CityOption[]
    citySearchStatus?: CitySearchStatus
    citySearchMessage?: string
    citySearchLoading?: boolean
    submitting?: boolean
  }>(),
  {
    cityOptions: () => [],
    citySearchStatus: 'idle',
    citySearchMessage: '',
    citySearchLoading: false,
    submitting: false,
  },
)

const emit = defineEmits<{
  submit: [value: DashboardQueryFormValues]
  searchCity: [query: string]
}>()

const forecastDayOptions = [3, 5, 7]
const aqForecastDayOptions = [3, 5]

const citySearchEmptyText = computed(() => {
  if (props.citySearchStatus === 'empty') {
    return '未找到匹配城市'
  }

  return '输入城市关键词搜索'
})

const citySearchNoMatchText = computed(() => {
  if (props.citySearchStatus === 'empty') {
    return '未找到匹配城市'
  }

  return '没有匹配的城市'
})

function handleCitySearch(query: string) {
  const trimmed = query.trim()
  if (!trimmed) {
    selectedLocation.value = null
  }
  emit('searchCity', trimmed)
}

function handleCityChange(value: string) {
  const matched = props.cityOptions.find((item) => item.value === value)
  selectedLocation.value = matched?.location ?? null
}

function handleSubmit() {
  emit('submit', {
    city: city.value.trim() || '成都',
    selectedLocation: selectedLocation.value,
    forecastDays: forecastDays.value,
    aqForecastDays: aqForecastDays.value,
    enableAnomalyDetection: enableAnomalyDetection.value,
    pm10Weight: pm10Weight.value,
  })
}

defineExpose({
  handleCitySearch,
  handleCityChange,
})
</script>

<template>
  <ElForm class="city-selector" label-position="top" @submit.prevent="handleSubmit">
    <div class="city-selector__grid">
      <ElFormItem class="city-selector__field city-selector__field--wide" label="选择城市">
        <ElSelect
          v-model="city"
          placeholder="输入城市关键词搜索"
          filterable
          remote
          reserve-keyword
          clearable
          class="city-selector__select"
          :loading="props.citySearchLoading"
          loading-text="正在搜索城市..."
          :no-data-text="citySearchEmptyText"
          :no-match-text="citySearchNoMatchText"
          :disabled="props.submitting"
          :remote-method="handleCitySearch"
          @change="handleCityChange"
        >
          <ElOption v-for="item in props.cityOptions" :key="item.label" :label="item.label" :value="item.value">
            <div class="city-selector__option">
              <span class="city-selector__option-label">{{ item.label }}</span>
              <ElTag v-if="item.badge" size="small" effect="plain" type="danger">{{ item.badge }}</ElTag>
            </div>
          </ElOption>
        </ElSelect>
        <p
          v-if="props.citySearchMessage"
          :class="['city-selector__helper', `city-selector__helper--${props.citySearchStatus}`]"
        >
          {{ props.citySearchMessage }}
        </p>
      </ElFormItem>

      <ElFormItem class="city-selector__field" label="天气预测天数">
        <ElSelect v-model="forecastDays" :disabled="props.submitting">
          <ElOption v-for="item in forecastDayOptions" :key="item" :label="`${item} 天`" :value="item" />
        </ElSelect>
      </ElFormItem>

      <ElFormItem class="city-selector__field" label="空气质量预测天数">
        <ElSelect v-model="aqForecastDays" :disabled="props.submitting">
          <ElOption v-for="item in aqForecastDayOptions" :key="item" :label="`${item} 天`" :value="item" />
        </ElSelect>
      </ElFormItem>

      <ElFormItem class="city-selector__field city-selector__field--switch" label="异常检测">
        <ElSwitch
          v-model="enableAnomalyDetection"
          inline-prompt
          active-text="开"
          inactive-text="关"
          :disabled="props.submitting"
        />
      </ElFormItem>

      <ElFormItem class="city-selector__field" label="PM10 权重">
        <ElInputNumber
          v-model="pm10Weight"
          class="city-selector__input-number"
          :min="0"
          :max="1"
          :step="0.05"
          :precision="2"
          :disabled="props.submitting"
          clearable
          placeholder="留空表示不参与评分"
          :value-on-clear="null"
        />
        <p class="city-selector__helper city-selector__helper--hint">可选参数，留空时不参与风险评分。</p>
      </ElFormItem>
    </div>

    <ElButton type="primary" native-type="submit" :loading="props.submitting">更新看板</ElButton>
  </ElForm>
</template>

<style scoped>
.city-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.city-selector__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px 16px;
}

.city-selector__select {
  width: 100%;
}

.city-selector__input-number {
  width: 100%;
}

.city-selector__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.city-selector__option-label {
  min-width: 0;
  flex: 1;
}

.city-selector__field {
  margin-bottom: 0;
}

.city-selector__field--wide {
  grid-column: span 4;
}

.city-selector__helper {
  width: 100%;
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.5;
}

.city-selector__helper--empty {
  color: var(--el-color-info);
}

.city-selector__helper--error {
  color: var(--el-color-warning);
}

.city-selector__helper--hint {
  color: var(--el-text-color-secondary);
}

.city-selector__field--switch :deep(.el-form-item__content) {
  min-height: 32px;
  align-items: center;
}

@media (max-width: 900px) {
  .city-selector__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .city-selector__field--wide {
    grid-column: span 2;
  }
}

@media (max-width: 600px) {
  .city-selector__grid {
    grid-template-columns: 1fr;
  }

  .city-selector__field--wide {
    grid-column: span 1;
  }
}
</style>
