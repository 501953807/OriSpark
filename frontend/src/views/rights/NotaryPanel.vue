<template>
  <div class="notary-panel">
    <div class="stats-row">
      <div class="stat-card"><div class="stat-val">{{ records.length }}</div><div class="stat-lbl">存证记录</div></div>
      <div class="stat-card"><div class="stat-val">{{ confirmed }}</div><div class="stat-lbl">已确认</div></div>
      <div class="stat-card"><div class="stat-val">{{ pending }}</div><div class="stat-lbl">待处理</div></div>
    </div>
    <div class="section-title">选择存证平台</div>
    <div class="platforms">
      <div v-for="p in platforms" :key="p.key" class="platform-card" @click="batchNotarize(p.key)">
        <div class="p-icon">{{ p.key === 'banquanjia' ? '🏛️' : p.key === 'antchain' ? '🐜' : '⚖️' }}</div>
        <div class="p-name">{{ p.name }}</div>
        <div class="p-fee">¥{{ p.fee_per_record }}/次</div>
        <div class="p-action">选择此平台 →</div>
      </div>
    </div>
    <div class="section-title">存证记录</div>
    <div v-if="records.length === 0" class="empty">🛡️ 暂无存证记录 — 选择平台开始存证</div>
    <div v-else class="record-list">
      <div v-for="r in records" :key="r.id" class="record-row">
        <span>{{ getWorkTitle(r.work_id) }}</span>
        <span>{{ r.platform }}</span>
        <span :class="['status', r.status]">{{ r.status === 'confirmed' ? '✅ 已存证' : r.status }}</span>
        <span>{{ r.created_at?.slice(0, 10) }}</span>
        <button v-if="r.status === 'pending'" @click="confirm(r.id)">确认</button>
        <button v-if="r.status === 'confirmed'" @click="viewCert(r)">证书</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useNotaryStore } from '@/stores/useNotaryStore'
import { useWorkStore } from '@/stores/useWorkStore'
const notary = useNotaryStore()
const work = useWorkStore()
const records = computed(() => notary.records)
const platforms = computed(() => notary.platforms)
const confirmed = computed(() => notary.records.filter((r:any) => r.status === 'confirmed').length)
const pending = computed(() => notary.records.filter((r:any) => r.status === 'pending').length)
function getWorkTitle(id: string) { return work.works.find((w:any) => w.id === id)?.title || id.slice(0,10) }
function batchNotarize(platform: string) {
  const unverified = work.works.filter((w:any) => !w.is_verified)
  if (unverified.length === 0) { alert('所有作品已存证'); return }
  notary.batchNotarize(unverified.map((w:any) => w.id), platform).then(() => notary.fetchRecords())
}
function confirm(id: string) { notary.confirmRecord(id).then(() => notary.fetchRecords()) }
function viewCert(r: any) { alert(`证书: ${r.certificates?.[0]?.cert_path || '生成中...'}`) }
onMounted(async () => { await Promise.all([notary.fetchRecords(), notary.fetchPlatforms(), work.fetchWorks()]) })
</script>
<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }
.stat-val { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-lbl { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.section-title { font-size: 1rem; font-weight: 700; margin: 20px 0 12px; }
.platforms { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.platform-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; cursor: pointer; transition: all 0.2s; text-align: center; }
.platform-card:hover { border-color: var(--accent); box-shadow: 0 2px 8px oklch(0 0 0 / 0.06); }
.p-icon { font-size: 2rem; margin-bottom: 8px; }
.p-name { font-weight: 600; font-size: 0.95rem; }
.p-fee { color: var(--accent); font-weight: 700; margin: 6px 0; }
.p-action { font-size: 0.8rem; color: var(--accent); }
.empty { padding: 48px; text-align: center; color: var(--muted); }
.record-list { display: flex; flex-direction: column; gap: 4px; }
.record-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 0.8fr; gap: 8px; align-items: center; padding: 10px 14px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; }
.status.confirmed { color: #1a7d36; font-weight: 600; }
.status.pending { color: #b8860b; }
</style>
