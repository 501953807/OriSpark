<template>
  <div class="craftsman-panel">
    <!-- Product Info -->
    <section class="info-group" v-if="productGroup.length">
      <h4 class="info-group-title">产品信息</h4>
      <div v-for="item in productGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Craft Specs -->
    <section class="info-group" v-if="craftGroup.length">
      <h4 class="info-group-title">工艺规格</h4>
      <div v-for="item in craftGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Dimensions -->
    <section class="info-group" v-if="dimGroup.length">
      <h4 class="info-group-title">尺寸重量</h4>
      <div v-for="item in dimGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Pricing & Production -->
    <section class="info-group" v-if="pricingGroup.length">
      <h4 class="info-group-title">定价与生产</h4>
      <div v-for="item in pricingGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyData" class="empty-hint">
      <span class="hint-icon">🔭</span>
      <p>暂无手工艺品数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Work } from '@/types/work'

interface Props {
  work: Work | null
  exifData: Record<string, any> | null
}

const props = withDefaults(defineProps<Props>(), {
  work: null,
  exifData: null,
})

const raw = computed(() => {
  if (props.exifData && typeof props.exifData === 'object') return props.exifData
  if (props.work?.custom_metadata?.crafts && typeof props.work.custom_metadata.crafts === 'object')
    return props.work.custom_metadata.crafts
  return null
})

const productMeta = computed(() => raw.value?.product ?? {})
const craftMeta = computed(() => raw.value?.craft ?? {})
const dimMeta = computed(() => raw.value?.dimensions ?? {})
const pricingMeta = computed(() => raw.value?.pricing ?? {})

const title = computed(() => productMeta.value?.title ?? props.work?.title ?? null)
const material = computed(() => craftMeta.value?.material ?? null)
const craftType = computed(() => craftMeta.value?.craft_type ?? null)
const moq = computed(() => productMeta.value?.moq ?? null)
const productionTime = computed(() => productMeta.value?.production_time_days ?? null)

const length = computed(() => dimMeta.value?.length ?? null)
const width = computed(() => dimMeta.value?.width ?? null)
const height = computed(() => dimMeta.value?.height ?? null)
const weight = computed(() => dimMeta.value?.weight ?? null)

const unitPrice = computed(() => pricingMeta.value?.unit_price ?? null)
const currency = computed(() => pricingMeta.value?.currency ?? 'CNY')
const stockQuantity = computed(() => productMeta.value?.stock_quantity ?? null)

function fmt(val: string | number | null | undefined): string {
  if (val == null || val === '') return '—'
  return String(val)
}

const productGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (title.value) items.push({ label: '标题', value: fmt(title.value) })
  if (moq.value != null) items.push({ label: '起订量', value: fmt(String(moq.value)) })
  if (stockQuantity.value != null) items.push({ label: '库存', value: fmt(String(stockQuantity.value)) })
  return items
})

const craftGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (material.value) items.push({ label: '材质', value: fmt(material.value) })
  if (craftType.value) items.push({ label: '工艺类型', value: fmt(craftType.value) })
  if (productionTime.value != null) items.push({ label: '生产周期', value: fmt(`${productionTime.value} 天`) })
  return items
})

const dimGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (length.value || width.value || height.value) {
    const dims = [length.value, width.value, height.value].filter(v => v != null)
    items.push({ label: '尺寸', value: fmt(dims.map(fmt).join(' x ')) })
  }
  if (weight.value != null) items.push({ label: '重量', value: fmt(`${weight.value} g`) })
  return items
})

const pricingGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (unitPrice.value != null) {
    const symbol = currency.value === 'USD' ? '$' : '¥'
    items.push({ label: '单价', value: fmt(`${symbol}${unitPrice.value}`) })
  }
  return items
})

const hasAnyData = computed(() => {
  return !!(
    title.value ||
    material.value ||
    craftType.value ||
    moq.value != null ||
    length.value ||
    width.value ||
    height.value ||
    weight.value != null ||
    unitPrice.value != null
  )
})
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--muted);
  gap: 8px;
}

.hint-icon { font-size: 2rem; opacity: 0.6; }

.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.info-group:last-child { border-bottom: none; padding-bottom: 0; }

.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.info-row:last-child { margin-bottom: 0; }

.info-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.8rem;
  min-width: 60px;
  flex-shrink: 0;
}

.info-value {
  color: var(--fg);
  font-size: 0.85rem;
  word-break: break-word;
}
</style>
