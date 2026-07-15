<template>
  <div class="monitor-panel">
    <div class="disclaimer-banner">⚠️ 本监测功能基于公开搜索引擎，不能保证发现所有侵权行为。相似度分数仅供参考，不构成侵权认定。监测结果需人工审核判断。</div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-val">{{ tasks.length }}</div><div class="stat-lbl">监测任务</div></div>
      <div class="stat-card"><div class="stat-val">{{ pending }}</div><div class="stat-lbl">待审核</div></div>
      <div class="stat-card"><div class="stat-val">{{ infringing }}</div><div class="stat-lbl">确认侵权</div></div>
    </div>
    <div class="toolbar">
      <select v-model="engine" class="select"><option value="baidu">百度识图</option><option value="google">Google Vision</option></select>
      <button class="btn btn-primary" @click="startScan">🔍 扫描未监测作品</button>
    </div>
    <div v-if="results.length === 0" class="empty">🔍 暂无监测结果 — 启动扫描开始监测</div>
    <div v-else class="result-grid">
      <div v-for="r in results" :key="r.id" class="result-card">
        <div class="r-sim">{{ (r as any).similarity_score || r.similarity || 0 }}%</div>
        <div class="r-title">{{ (r as any).matched_title || (r as any).title || '未知' }}</div>
        <div class="r-url">{{ r.matched_url || (r as any).url || '-' }}</div>
        <div class="r-date">{{ r.found_at?.slice(0, 10) || (r as any).created_at?.slice(0, 10) }}</div>
        <div class="r-actions">
          <button class="btn-sm btn-danger" @click="judge(r.id, 'infringing')">确认侵权</button>
          <button class="btn-sm" @click="judge(r.id, 'ignored')">标记误报</button>
          <button class="btn-sm" @click="judge(r.id, 'whitelisted')">白名单</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMonitorStore } from '@/stores/useMonitorStore'
import { useWorkStore } from '@/stores/useWorkStore'
const monitor = useMonitorStore()
const work = useWorkStore()
const engine = ref('baidu')
const tasks = computed(() => monitor.tasks || [])
const results = computed(() => monitor.results || [])
const pending = computed(() => (monitor.results || []).filter((r: any) => r.status === 'pending_review').length)
const infringing = computed(() => (monitor.results || []).filter((r: any) => r.status === 'infringing').length)
function startScan() {
  monitor.batchScan(work.works.map((w: any) => w.id), engine.value).then(() => monitor.fetchResults())
}
function judge(id: string, status: 'pending_review' | 'infringing' | 'ignored' | 'whitelisted') { monitor.updateResult(id, { status }).then(() => monitor.fetchResults()) }
onMounted(async () => { await Promise.all([monitor.fetchTasks(), monitor.fetchResults(), work.fetchWorks()]) })
</script>
<style scoped>
.disclaimer-banner { background: #fff8e1; border: 1px solid #f0c040; color: #6d4c00; padding: 10px 16px; border-radius: var(--radius-sm); font-size: 0.82rem; margin-bottom: 16px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }
.stat-val { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-lbl { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 16px; }
.select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.btn { padding: 8px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem; }
.btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.empty { padding: 48px; text-align: center; color: var(--muted); }
.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; }
.result-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.r-sim { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
.r-title { font-weight: 600; margin: 6px 0 2px; }
.r-url { font-size: 0.78rem; color: var(--muted); word-break: break-all; margin-bottom: 8px; }
.r-date { font-size: 0.75rem; color: var(--muted); margin-bottom: 8px; }
.r-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-sm { padding: 4px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.78rem; cursor: pointer; }
.btn-danger { background: #fde8e8; border-color: #e57373; color: #c62828; }
</style>
