<template>
  <div class="product-card">
    <div class="card-body">
      <div class="card-header">
        <h3 class="product-title">{{ product.title || '未命名作品' }}</h3>
        <span
          class="craft-badge"
          :style="{ backgroundColor: badgeColor }"
        >
          {{ badgeLabel }}
        </span>
      </div>

      <div class="card-details">
        <div v-if="product.material" class="detail-row">
          <span class="detail-label">材质</span>
          <span class="detail-value">{{ product.material }}</span>
        </div>

        <div class="detail-row">
          <span class="detail-label">MOQ</span>
          <span class="detail-value">{{ product.moq }} 件</span>
        </div>

        <div v-if="product.unit_price != null" class="detail-row">
          <span class="detail-label">单价</span>
          <span class="detail-value price">{{ formatPrice(product.unit_price) }}</span>
        </div>

        <div v-if="product.production_time_days != null" class="detail-row">
          <span class="detail-label">生产周期</span>
          <span class="detail-value">{{ product.production_time_days }} 天</span>
        </div>
      </div>

      <div v-if="hasDimensions" class="dimensions">
        <span v-if="product.dimensions?.length != null">{{ product.dimensions!.length }}mm</span>
        <span v-if="product.dimensions?.width != null"> x {{ product.dimensions!.width }}mm</span>
        <span v-if="product.dimensions?.height != null"> x {{ product.dimensions!.height }}mm</span>
        <span v-if="product.dimensions?.weight != null" class="weight">| {{ product.dimensions!.weight }}g</span>
      </div>
    </div>

    <div class="card-footer">
      <button class="btn btn-ghost btn-sm" @click="$emit('edit', product)">
        <span class="icon">&nbsp;&#9998;&nbsp;</span> 编辑
      </button>
      <button class="btn btn-ghost btn-sm btn-danger" @click="$emit('delete', product)">
        <span class="icon">&nbsp;&#128465;&nbsp;</span> 删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CraftProduct } from '@/types/craftsman'

const CRAFT_TYPE_LABELS: Record<string, string> = {
  embroidery: '刺绣',
  ceramics: '陶瓷',
  woodcarving: '木雕',
  weaving: '编织',
  pottery: '陶艺',
  other: '其他',
}

const CRAFT_TYPE_COLORS: Record<string, string> = {
  embroidery: '#d946ef',
  ceramics: '#f59e0b',
  woodcarving: '#92400e',
  weaving: '#059669',
  pottery: '#dc2626',
  other: '#6b7280',
}

interface Props {
  product: CraftProduct
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [product: CraftProduct]
  delete: [product: CraftProduct]
}>()

const badgeLabel = computed(
  () => CRAFT_TYPE_LABELS[props.product.craft_type] ?? props.product.craft_type,
)
const badgeColor = computed(
  () => CRAFT_TYPE_COLORS[props.product.craft_type] ?? CRAFT_TYPE_COLORS.other,
)
const hasDimensions = computed(
  () =>
    props.product.dimensions &&
    (props.product.dimensions.length != null ||
      props.product.dimensions.width != null ||
      props.product.dimensions.height != null ||
      props.product.dimensions.weight != null),
)

function formatPrice(price: number): string {
  return `¥${price.toFixed(2)}`
}
</script>

<style scoped>
.product-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.15s;
}

.product-card:hover {
  box-shadow: 0 4px 20px oklch(0 0 0 / 0.06);
  transform: translateY(-1px);
}

/* ── Body ───────────────────────────────────────────────────── */
.card-body {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.product-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Craft type badge ───────────────────────────────────────── */
.craft-badge {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #fff;
  line-height: 1.4;
}

/* ── Detail rows ────────────────────────────────────────────── */
.card-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.84rem;
}

.detail-label {
  color: var(--muted);
  font-size: 0.78rem;
}

.detail-value {
  font-weight: 500;
  color: var(--fg);
}

.detail-value.price {
  color: var(--accent);
  font-weight: 700;
}

.dimensions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  font-size: 0.76rem;
  color: var(--muted);
}

.weight {
  margin-left: 4px;
}

/* ── Footer ─────────────────────────────────────────────────── */
.card-footer {
  display: flex;
  gap: 0;
  border-top: 1px solid var(--border);
}

.card-footer .btn {
  flex: 1;
  border: none;
  border-radius: 0;
  justify-content: center;
}

.icon {
  font-size: 0.82rem;
}

.btn-sm {
  padding: 8px 12px;
  font-size: 0.8rem;
}

.btn-danger:hover {
  color: #ef4444;
  background: oklch(95% 0.02 0 / 0.5);
}
</style>
