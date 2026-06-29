<template>
  <div class="notary-view">
    <!-- Stats -->
    <div class="stats-row">
      <StatCard icon="📊" label="存证记录" :value="notaryStore.records.length" color="green" />
      <StatCard icon="✅" label="已确认" :value="confirmedCount" color="purple" />
      <StatCard icon="⏳" label="待处理" :value="pendingCount" color="orange" />
    </div>

    <!-- Platforms -->
    <div class="section-title">存证平台</div>
    <div class="platforms-grid">
      <div v-for="p in platforms" :key="p.key" class="platform-card card">
        <div class="platform-header">
          <div class="platform-icon" :class="`icon-${p.legal_level}`">
            {{ p.key === 'banquanjia' ? '🏛️' : p.key === 'antchain' ? '🐜' : '⚖️' }}
          </div>
          <div>
            <div class="platform-name">{{ p.name }}</div>
            <div class="platform-level">{{ legalLevelLabels[p.legal_level] }}</div>
          </div>
        </div>
        <div class="platform-desc">{{ p.description }}</div>
        <div class="platform-meta">
          <span class="platform-fee">¥{{ p.fee_per_record }}/次</span>
          <StatusBadge :status="p.is_available ? 'active' : 'inactive'" :labels="{ active: '可用', inactive: '不可用' }" :variants="{ active: 'success', inactive: 'error' }" />
        </div>
        <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" @click="startNotary(p.key)">
          选择此平台存证
        </button>
      </div>
    </div>

    <!-- Records table -->
    <div class="section-title">存证记录</div>
    <div v-if="notaryStore.loading"><LoadingSpinner text="加载中..." /></div>
    <EmptyState v-else-if="notaryStore.records.length === 0" icon="🔒" title="暂无存证记录" description="选择作品和平台，开始存证确权" />

    <div v-else class="records-table card">
      <div class="table-header">
        <span class="col-work">作品</span>
        <span class="col-platform">平台</span>
        <span class="col-hash">存证哈希</span>
        <span class="col-status">状态</span>
        <span class="col-fee">费用</span>
        <span class="col-date">日期</span>
        <span class="col-actions">操作</span>
      </div>
      <div v-for="r in notaryStore.records" :key="r.id" class="table-row">
        <span class="col-work" :title="r.work_id">{{ getWorkTitle(r.work_id) }}</span>
        <span class="col-platform">{{ platformNames[r.platform] || r.platform }}</span>
        <span class="col-hash mono">{{ r.evidence_hash?.slice(0, 12) || '—' }}</span>
        <span class="col-status">
          <StatusBadge :status="r.status" :labels="statusLabels" :variants="statusVariants" />
        </span>
        <span class="col-fee">¥{{ r.fee }}</span>
        <span class="col-date">{{ r.created_at?.slice(0, 10) }}</span>
        <span class="col-actions">
          <button v-if="r.status === 'pending'" class="btn btn-primary btn-sm" @click="confirmRecord(r.id)">确认存证</button>
          <button v-if="r.status === 'confirmed'" class="btn btn-secondary btn-sm" @click="viewCertificate(r)">查看证书</button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useNotaryStore } from '@/stores/useNotaryStore'
import { useWorkStore } from '@/stores/useWorkStore'
import type { NotaryRecord } from '@/types/notary'

const notaryStore = useNotaryStore()
const workStore = useWorkStore()

const platforms = computed(() => notaryStore.platforms)

// Build a work title lookup map
const workTitleMap = computed(() => {
  const map: Record<string, string> = {}
  for (const w of workStore.works) {
    map[w.id] = w.title
  }
  return map
})

function getWorkTitle(workId: string): string {
  return workTitleMap.value[workId] || workId.slice(0, 12)
}

const confirmedCount = computed(() =>
  notaryStore.records.filter((r: NotaryRecord) => r.status === 'confirmed').length
)
const pendingCount = computed(() =>
  notaryStore.records.filter((r: NotaryRecord) => r.status === 'pending').length
)

const legalLevelLabels: Record<string, string> = {
  national: '国家级 · 法律效力最高',
  judicial: '司法级 · 互联网法院认可',
  commercial: '商用级 · 区块链存证',
}

const platformNames: Record<string, string> = {
  banquanjia: '版权家',
  antchain: '蚂蚁链',
  zhixinchain: '至信链',
}

const statusLabels: Record<string, string> = {
  unverified: '未存证',
  pending: '待确认',
  confirmed: '已确认',
  failed: '失败',
  expired: '已过期',
}

const statusVariants: Record<string, string> = {
  unverified: 'info',
  pending: 'warning',
  confirmed: 'success',
  failed: 'error',
  expired: 'default',
}

function startNotary(platform: string) {
  const works = workStore.works
  if (works.length === 0) {
    ;(window as any).$toast?.show('请先导入作品', 'warning')
    return
  }
  // 批量存证所有未存证作品
  const unverified = works.filter(w => !w.is_verified)
  if (unverified.length === 0) {
    ;(window as any).$toast?.show('所有作品已存证', 'info')
    return
  }
  notaryStore.batchNotarize(unverified.map(w => w.id), platform).then(async () => {
    ;(window as any).$toast?.show(`已创建 ${unverified.length} 条存证记录`, 'success')
    await notaryStore.fetchRecords()
  })
}

async function confirmRecord(id: string) {
  await notaryStore.confirmRecord(id)
  ;(window as any).$toast?.show('存证已确认，证书已生成', 'success')
}

function viewCertificate(record: NotaryRecord) {
  if (record.certificates?.length) {
    const cert = record.certificates[0]
    ;(window as any).$toast?.show(`证书路径: ${cert.cert_path}`, 'info')
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      notaryStore.fetchRecords(),
      notaryStore.fetchPlatforms(),
      workStore.fetchWorks(),
    ])
  } catch {
    ;(window as any).$toast?.show('加载存证数据失败', 'error')
  }
})
</script>

<style scoped>
.notary-view { display: flex; flex-direction: column; gap: 24px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 768px) { .stats-row { grid-template-columns: 1fr; } }
.section-title { font-size: 1rem; font-weight: 700; font-family: var(--font-display); }
.platforms-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 1024px) { .platforms-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) { .platforms-grid { grid-template-columns: 1fr; } }
.platform-card { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.platform-header { display: flex; align-items: center; gap: 12px; }
.platform-icon {
  width: 44px; height: 44px; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; flex-shrink: 0;
}
.icon-national { background: oklch(56% 0.12 170 / 0.12); }
.icon-judicial { background: oklch(58% 0.16 280 / 0.12); }
.icon-commercial { background: oklch(58% 0.14 245 / 0.12); }
.platform-name { font-weight: 700; font-size: 0.95rem; }
.platform-level { font-size: 0.68rem; color: var(--muted); }
.platform-desc { font-size: 0.82rem; color: var(--muted); line-height: 1.5; }
.platform-meta { display: flex; align-items: center; justify-content: space-between; }
.platform-fee { font-weight: 700; color: var(--accent); font-size: 0.9rem; }
.records-table { overflow-x: auto; padding: 0; }
.table-header, .table-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1.2fr 1fr 0.8fr 1fr 1fr;
  gap: 8px;
  align-items: center;
  padding: 12px 16px;
  font-size: 0.82rem;
}
.table-header { font-weight: 700; color: var(--muted); border-bottom: 1px solid var(--border); }
.table-row { border-bottom: 1px solid oklch(93% 0.003 240); }
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: oklch(97% 0.002 240); }
.mono { font-family: monospace; font-size: 0.75rem; }
.btn-sm { padding: 6px 14px; font-size: 0.8rem; }
</style>
