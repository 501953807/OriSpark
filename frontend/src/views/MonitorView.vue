<template>
  <div class="monitor-view">
    <!-- Tab Navigation -->
    <div class="tabs-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'scan' }"
        @click="activeTab = 'scan'"
      >侵权扫描</button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'brand' }"
        @click="activeTab = 'brand'"
      >品牌监测</button>
    </div>

    <!-- Scan Tab -->
    <div v-if="activeTab === 'scan'">
      <DisclaimerBanner
        mode="banner"
        title="侵权监测局限性（声明 #6）"
        :messages="['系统通过第三方API检测，不能保证发现所有侵权行为。未检测到不代表不存在侵权。检测结果仅供参考，法律行动前应咨询律师。']"
      />
      <!-- Stats -->
      <div class="stats-row">
        <StatCard icon="🔍" label="监测任务" :value="monitorStore.tasks.length" color="green" />
        <StatCard icon="⚠️" label="待审核" :value="pendingResults.length" color="orange" />
        <StatCard icon="❌" label="确认侵权" :value="infringingCount" color="orange" />
      </div>

      <!-- Scan actions -->
      <div class="scan-actions card">
        <div class="scan-info">
          <div class="scan-title">手动扫描</div>
          <div class="scan-desc">选择作品，通过百度识图/Google Vision 搜索相似内容</div>
        </div>
        <div class="scan-controls">
          <select v-model="scanPlatform" class="filter-select">
            <option value="baidu">百度识图 (100次/天)</option>
            <option value="google">Google Vision (1000次/月)</option>
          </select>
          <button class="btn btn-primary" @click="handleBatchScan" :disabled="!hasUnscannedWorks">
            扫描全部未监测作品
          </button>
        </div>
      </div>

      <!-- Results -->
      <div class="section-title">监测结果</div>
      <div v-if="monitorStore.loading"><LoadingSpinner text="扫描中..." /></div>
      <EmptyState v-else-if="monitorStore.results.length === 0" icon="🛡️" title="暂无监测结果" description="选择作品和平台，开始侵权监测">
        <button class="btn btn-primary" style="margin-top:16px" @click="handleBatchScan">🔍 开始扫描</button>
      </EmptyState>

      <div v-else class="results-grid">
        <div v-for="result in monitorStore.results" :key="result.id" class="result-card card">
          <div class="result-header">
            <StatusBadge :status="result.status" :labels="resultStatusLabels" :variants="resultStatusVariants" />
            <span class="result-similarity" :class="getSimilarityClass(result.similarity)">
              {{ result.similarity.toFixed(1) }}% 相似
            </span>
          </div>
          <div class="result-title">{{ result.matched_title || '未命名匹配' }}</div>
          <div class="result-url mono">{{ result.matched_url }}</div>
          <div class="result-date">发现时间: {{ result.found_at?.slice(0, 16) }}</div>
          <div v-if="result.status === 'pending_review'" class="result-actions">
            <button class="btn btn-secondary btn-sm" @click="handleResult(result.id, 'infringing')">确认侵权</button>
            <button class="btn btn-ghost btn-sm" @click="handleResult(result.id, 'ignored', '误报')">标记误报</button>
            <button class="btn btn-ghost btn-sm" @click="handleResult(result.id, 'whitelisted')">加入白名单</button>
          </div>
          <div v-else class="result-taken">
            {{ result.action_taken || resultStatusLabels[result.status] }}
          </div>
        </div>
      </div>

      <!-- Quota info -->
      <div v-if="monitorStore.quota" class="quota-bar">
        <div class="quota-item">
          🔍 百度识图: {{ monitorStore.quota.baidu.used_today }}/{{ monitorStore.quota.baidu.daily_limit }} (今日)
        </div>
        <div class="quota-item">
          🤖 Google Vision: {{ monitorStore.quota.google.used_this_month }}/{{ monitorStore.quota.google.monthly_limit }} (本月)
        </div>
      </div>
    </div>

    <!-- Brand Tab -->
    <div v-if="activeTab === 'brand'">
      <BrandWatchPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import DisclaimerBanner from '@/components/common/DisclaimerBanner.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import BrandWatchPanel from '@/components/monitor/BrandWatchPanel.vue'
import { useMonitorStore } from '@/stores/useMonitorStore'
import { useWorkStore } from '@/stores/useWorkStore'
import type { MonitorResult } from '@/types/monitor'

const monitorStore = useMonitorStore()
const workStore = useWorkStore()

const activeTab = ref<'scan' | 'brand'>('scan')
const scanPlatform = ref('baidu')

const hasUnscannedWorks = computed(() => workStore.works.length > 0)
const pendingResults = computed(() => monitorStore.results.filter((r: MonitorResult) => r.status === 'pending_review'))
const infringingCount = computed(() => monitorStore.results.filter((r: MonitorResult) => r.status === 'infringing').length)

const resultStatusLabels: Record<string, string> = {
  pending_review: '待审核',
  infringing: '确认侵权',
  ignored: '已忽略',
  whitelisted: '白名单',
}

const resultStatusVariants: Record<string, string> = {
  pending_review: 'warning',
  infringing: 'error',
  ignored: 'default',
  whitelisted: 'success',
}

function getSimilarityClass(sim: number): string {
  if (sim >= 80) return 'high'
  if (sim >= 50) return 'mid'
  return 'low'
}

async function handleBatchScan() {
  const workIds = workStore.works.map(w => w.id)
  if (workIds.length === 0) {
    ;(window as any).$toast?.show('请先导入作品', 'warning')
    return
  }
  try {
    await monitorStore.batchScan(workIds, scanPlatform.value)
    await monitorStore.fetchResults()
    ;(window as any).$toast?.show('扫描完成，请查看下方结果', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show('扫描失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

async function handleResult(id: string, status: string, reason?: string) {
  try {
    await monitorStore.updateResult(id, { status, ignore_reason: reason })
    await monitorStore.fetchResults()
    ;(window as any).$toast?.show('结果已更新', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show('更新失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

onMounted(async () => {
  try {
    await workStore.fetchWorks()
    await monitorStore.fetchResults()
    await monitorStore.fetchQuota()
  } catch (e: any) {
    ;(window as any).$toast?.show('加载监测数据失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
})
</script>

<style scoped>
.monitor-view { display: flex; flex-direction: column; gap: 24px; }
.tabs-bar { display: flex; gap: 0; border-bottom: 2px solid var(--border); }
.tab-btn {
  padding: 10px 24px; font-size: 0.9rem; font-weight: 600;
  font-family: var(--font-body); border: none; background: none; color: var(--muted);
  cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
}
.tab-btn:hover { color: var(--fg); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 768px) { .stats-row { grid-template-columns: 1fr; } }
.section-title { font-size: 1rem; font-weight: 700; font-family: var(--font-display); }
.scan-actions { padding: 20px; display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.scan-title { font-weight: 700; font-size: 0.95rem; }
.scan-desc { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.scan-controls { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.filter-select {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); color: var(--fg); font-size: 0.85rem;
  font-family: var(--font-body); cursor: pointer;
}
.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.result-card { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.result-header { display: flex; align-items: center; justify-content: space-between; }
.result-similarity { font-weight: 700; font-size: 0.9rem; }
.result-similarity.high { color: #e53e3e; }
.result-similarity.mid { color: var(--orange); }
.result-similarity.low { color: var(--muted); }
.result-title { font-weight: 700; font-size: 0.9rem; }
.result-url { font-size: 0.75rem; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-date { font-size: 0.72rem; color: var(--muted); }
.result-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.result-taken { font-size: 0.82rem; color: var(--muted); }
.btn-sm { padding: 6px 12px; font-size: 0.78rem; }
.mono { font-family: monospace; }
.quota-bar { display: flex; gap: 24px; padding: 12px 16px; background: oklch(96% 0.003 240); border-radius: var(--radius); font-size: 0.82rem; color: var(--muted); }
</style>
