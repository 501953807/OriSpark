<!-- RevenuePanel — 收入追踪

Shows revenue records for a listing with monthly trend chart.
Supports manual entry and CSV import hint.
-->
<template>
  <div class="revenue-panel">
    <div class="panel-header">
      <h4>💰 收入追踪</h4>
      <button class="btn-add" @click="showAddRevenue = true">+ 录入收入</button>
    </div>

    <!-- Summary cards -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="summary-label">累计收入</div>
        <div class="summary-value">¥{{ totalRevenue }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">本月收入</div>
        <div class="summary-value">¥{{ monthRevenue }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">平均利润率</div>
        <div class="summary-value">{{ avgMargin }}%</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">记录数</div>
        <div class="summary-value">{{ revenues.length }}</div>
      </div>
    </div>

    <!-- Monthly trend bar chart -->
    <div v-if="monthlyData.length" class="trend-chart">
      <h5>近 12 个月趋势</h5>
      <div class="chart-bars">
        <div v-for="m in monthlyData" :key="m.month" class="bar-wrapper">
          <div class="bar" :style="{ height: barHeight(m.revenue) + 'px' }" :title="'¥' + m.revenue"></div>
          <div class="bar-label">{{ m.month }}</div>
        </div>
      </div>
    </div>

    <!-- Revenue list -->
    <div class="revenue-table">
      <table>
        <thead>
          <tr>
            <th>日期</th>
            <th>平台</th>
            <th>金额</th>
            <th>净收入</th>
            <th>来源</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in revenues" :key="r.id">
            <td>{{ formatDate(r.date) }}</td>
            <td>{{ r.platform || '-' }}</td>
            <td class="amount">¥{{ r.amount }}</td>
            <td>¥{{ r.net_revenue ?? '-' }}</td>
            <td><span class="source-tag">{{ sourceLabel(r.source) }}</span></td>
            <td class="notes">{{ r.notes || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add revenue dialog -->
    <div v-if="showAddRevenue" class="modal-overlay" @click.self="showAddRevenue = false">
      <div class="modal">
        <h4>录入收入</h4>
        <div class="form-group">
          <label>金额</label>
          <input v-model.number="form.amount" type="number" class="form-input" />
        </div>
        <div class="form-group">
          <label>平台</label>
          <select v-model="form.platform" class="form-select">
            <option value="printful">Printful</option>
            <option value="redbubble">Redbubble</option>
            <option value="modian">摩点</option>
            <option value="other">其他</option>
          </select>
        </div>
        <div class="form-group">
          <label>日期</label>
          <input v-model="form.date" type="date" class="form-input" />
        </div>
        <div class="form-group">
          <label>来源</label>
          <select v-model="form.source" class="form-select">
            <option value="manual">手动录入</option>
            <option value="csv_import">CSV 导入</option>
          </select>
        </div>
        <div class="form-group">
          <label>备注</label>
          <input v-model="form.notes" class="form-input" placeholder="可选" />
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="showAddRevenue = false">取消</button>
          <button class="btn-save" @click="saveRevenue" :disabled="saving">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBusinessStore } from '@/stores/useBusinessStore'
import type { RevenueRecord } from '@/types/business'

interface Props {
  listingId: string
}
defineProps<Props>()

interface RevRecord extends RevenueRecord {
  source?: string
  notes?: string
  platform?: string
  net_revenue?: number
}

const businessStore = useBusinessStore()
const saving = ref(false)
const showAddRevenue = ref(false)

const revenues = computed(() => businessStore.revenues as unknown as RevRecord[])

const form = ref({
  amount: 0, platform: 'printful', date: new Date().toISOString().split('T')[0],
  source: 'manual', notes: '',
})

const totalRevenue = computed(() => revenues.value.reduce((s, r) => s + r.amount, 0).toFixed(2))

const monthRevenue = computed(() => {
  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return revenues.value
    .filter(r => r.date?.startsWith(ym))
    .reduce((s, r) => s + r.amount, 0).toFixed(2)
})

const avgMargin = computed(() => {
  if (!revenues.value.length) return 0
  const totalNet = revenues.value.reduce((s, r) => s + (r.net_revenue || r.amount * 0.7), 0)
  const totalAmt = revenues.value.reduce((s, r) => s + r.amount, 0)
  return totalAmt ? Math.round((totalNet / totalAmt) * 100) : 0
})

const monthlyData = computed(() => {
  const months: Record<string, number> = {}
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    months[key] = 0
  }
  revenues.value.forEach(r => {
    const k = r.date?.substring(0, 7)
    if (k && months[k] !== undefined) months[k] += r.amount
  })
  return Object.entries(months)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([month, revenue]) => ({ month, revenue }))
})

function barHeight(val: number): number {
  const max = Math.max(...Object.values(monthlyData.value.reduce((acc, m) => ({ ...acc, [m.month]: m.revenue }), {} as Record<string, number>)), 1)
  return Math.max(4, (val / max) * 120)
}

function formatDate(d: string | null): string {
  return d ? new Date(d).toLocaleDateString('zh-CN') : '-'
}

function sourceLabel(s?: string): string {
  const map: Record<string, string> = { manual: '手动', csv_import: 'CSV导入', auto_sync: '自动同步' }
  return map[s || ''] || s || '-'
}

async function saveRevenue() {
  saving.value = true
  try {
    await businessStore.addRevenue({
      amount: form.value.amount,
      date: form.value.date,
      platform: form.value.platform,
      source: form.value.source,
      notes: form.value.notes,
    })
    showAddRevenue.value = false
  } catch {
    ;(window as any).$toast?.show('保存收入失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  businessStore.fetchRevenues()
})
</script>

<style scoped>
.revenue-panel { padding: 0 4px; }

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.panel-header h4 { margin: 0; font-size: .9rem; }

.btn-add {
  background: var(--accent); color: #fff; border: none;
  padding: 4px 12px; border-radius: var(--radius-sm); font-size: .78rem; cursor: pointer;
}

.summary-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  margin-bottom: 16px;
}

.summary-card {
  padding: 10px 12px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface); text-align: center;
}

.summary-label { font-size: .68rem; color: var(--muted); }
.summary-value { font-size: 1.1rem; font-weight: 800; color: var(--accent); margin-top: 2px; }

/* Trend chart */
.trend-chart { margin-bottom: 16px; }
.trend-chart h5 { font-size: .82rem; margin: 0 0 8px; }

.chart-bars {
  display: flex; gap: 4px; align-items: flex-end; height: 140px;
  padding: 0 4px;
}

.bar-wrapper {
  flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%;
  justify-content: flex-end;
}

.bar {
  width: 100%; max-width: 32px; background: var(--accent); border-radius: 3px 3px 0 0;
  transition: height 0.3s; min-height: 4px;
}

.bar-label { font-size: .58rem; color: var(--muted); margin-top: 4px; white-space: nowrap; }

/* Table */
.revenue-table { overflow-x: auto; }

.revenue-table table {
  width: 100%; border-collapse: collapse; font-size: .78rem;
}

.revenue-table th {
  text-align: left; padding: 8px; border-bottom: 2px solid var(--border);
  color: var(--muted); font-weight: 600;
}

.revenue-table td {
  padding: 8px; border-bottom: 1px solid var(--border);
}

.amount { font-weight: 700; color: var(--accent); }
.source-tag {
  padding: 1px 6px; border-radius: 100px; font-size: .65rem;
  background: var(--muted-bg);
}
.notes { color: var(--muted); max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(20% 0.02 180 / .5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}

.modal {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 24px; width: 400px; max-width: 90vw;
}

.modal h4 { margin: 0 0 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-select, .form-input {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .85rem; background: var(--surface);
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}
.btn-save {
  padding: 6px 16px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; cursor: pointer; font-size: .82rem;
}
</style>
