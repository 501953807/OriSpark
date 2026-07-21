<script setup lang="ts">
import { ref, computed } from 'vue'
import { supplyApi } from '@/api/supply'
import { listingBatchApi } from '@/api/marketplace'
import type { ListingDetail } from '@/types/supply'

const props = defineProps<{ listings: ListingDetail[] }>()
const emit = defineEmits<{ refresh: [] }>()

const selectedIds = ref<Set<string>>(new Set())
const showBatchPanel = ref(false)

const hasSelection = computed(() => selectedIds.value.size > 0)

const toggleSelect = (id: string) => {
  const s = new Set(selectedIds.value)
  if (s.has(id)) {
    s.delete(id)
  } else {
    s.add(id)
  }
  selectedIds.value = s
}

const selectAll = () => {
  if (selectedIds.value.size === props.listings.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(props.listings.map(l => l.id))
  }
}

async function doToggleStatus(status: string) {
  try {
    await listingBatchApi.toggleStatus({ ids: [...selectedIds.value], status })
    emit('refresh')
    selectedIds.value = new Set()
  } catch { /* handled by interceptor */ }
}

async function doExpire() {
  try {
    await listingBatchApi.expire({ ids: [...selectedIds.value] })
    emit('refresh')
    selectedIds.value = new Set()
  } catch { /* handled by interceptor */ }
}
</script>

<template>
  <div v-if="showBatchPanel" class="batch-listing-panel card">
    <div class="panel-header">
      <h3>批量操作（已选 {{ selectedIds.size }} 项）</h3>
      <button class="btn-ghost btn-xs" @click="showBatchPanel = false">关闭</button>
    </div>
    <div class="batch-actions">
      <button class="btn btn-sm btn-primary" @click="doToggleStatus('active')">上架</button>
      <button class="btn btn-sm btn-secondary" @click="doToggleStatus('draft')">草稿</button>
      <button class="btn btn-sm btn-warning" @click="doExpire">过期下架</button>
    </div>
    <div class="listing-checklist">
      <label v-for="l in listings" :key="l.id" class="check-item">
        <input
          type="checkbox"
          :checked="selectedIds.has(l.id)"
          @change="toggleSelect(l.id)"
        />
        <span>{{ l.title }}</span>
        <span class="status-chip" :class="l.status">{{ l.status }}</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.batch-listing-panel { padding: 16px; margin-bottom: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.batch-actions { display: flex; gap: 8px; margin-bottom: 12px; }
.check-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 0.85rem; }
.status-chip { font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; }
</style>
