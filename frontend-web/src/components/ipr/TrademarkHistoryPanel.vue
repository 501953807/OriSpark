<template>
  <div class="tm-history-panel">
    <div class="panel-title">📋 查询历史</div>
    <div class="filter-bar">
      <select v-model="filterJurisdiction" class="form-input" size="small">
        <option value="">全部辖区</option>
        <option value="cn">🇨🇳 中国</option>
        <option value="us">🇺🇸 美国</option>
        <option value="eu">🇪🇺 欧盟</option>
        <option value="wipo">🌐 WIPO</option>
      </select>
      <button class="btn btn-sm btn-secondary" @click="loadHistory">刷新</button>
    </div>
    <div v-if="records.length === 0" class="empty">
      暂无查询记录
    </div>
    <div v-else class="history-list">
      <div v-for="r in records" :key="r.id" class="history-item">
        <div class="history-main">
          <span class="history-text">{{ r.query_text }}</span>
          <span class="history-meta">{{ r.jurisdiction }} · {{ r.result_count }}条结果 · {{ formatDate(r.created_at) }}</span>
        </div>
        <button class="btn btn-sm btn-secondary" @click="rerunQuery(r)">重新查询</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { iprApi } from '@/api/ipr'

const props = defineProps<{
  userId?: string
}>()

const emit = defineEmits<{
  rerun: [record: any]
}>()

const records = ref<any[]>([])
const filterJurisdiction = ref('')

async function loadHistory() {
  try {
    const res = await iprApi.trademarkHistory({
      user_id: props.userId || 'local',
      jurisdiction: filterJurisdiction.value || undefined,
      limit: 20,
    })
    records.value = res.data?.data || []
  } catch {
    records.value = []
  }
}

function formatDate(isoStr: string | null): string {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString('zh-CN')
}

function rerunQuery(record: any) {
  emit('rerun', record)
}

watch(filterJurisdiction, () => loadHistory())
onMounted(loadHistory)
</script>

<style scoped>
.tm-history-panel { padding: 16px 0; }
.panel-title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 12px; }
.history-list { display: flex; flex-direction: column; gap: 6px; }
.history-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  font-size: 0.82rem;
}
.history-main { display: flex; flex-direction: column; gap: 2px; }
.history-text { font-weight: 600; }
.history-meta { color: var(--muted); font-size: 0.78rem; }
.empty { color: var(--muted); font-size: 0.85rem; text-align: center; padding: 20px 0; }
</style>
