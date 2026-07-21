<template>
  <div class="business-view">
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-icon">💰</div><div class="stat-value">¥{{ stats.totalRevenue?.toLocaleString() || '0' }}</div><div class="stat-label">总收入</div></div>
      <div class="stat-card"><div class="stat-icon">📅</div><div class="stat-value">¥{{ stats.monthlyRevenue?.toLocaleString() || '0' }}</div><div class="stat-label">本月收入</div></div>
      <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">{{ stats.productCount || 0 }}</div><div class="stat-label">产品数</div></div>
      <div class="stat-card"><div class="stat-icon">👥</div><div class="stat-value">{{ stats.partnerCount || 0 }}</div><div class="stat-label">合作伙伴</div></div>
    </div>
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.key" :class="['tab-btn', { active: activeTab === tab.key }]" @click="activeTab = tab.key">{{ tab.icon }} {{ tab.label }}<span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span></button>
    </div>

    <!-- Revenue Tab -->
    <div v-if="activeTab === 'revenue'" class="tab-content">
      <div class="toolbar">
        <button class="btn btn-primary" @click="showAddRevenue = true">💵 手动登记</button>
        <button class="btn btn-secondary" @click="triggerCsvImport">📥 CSV导入</button>
        <input ref="csvInputRef" type="file" accept=".csv" hidden @change="handleCsvImport" />
      </div>
      <EmptyState v-if="!loading && revenues.length === 0" icon="💰" title="收入数据将自动汇总" description="创建产品并在POD渠道上架后，收入记录会出现在这里" :show-action="true" :primary-action="{ label: '💵 手动登记', onClick: () => showAddRevenue = true }" />
      <div v-else class="revenue-list">
        <div v-for="r in revenues" :key="r.id" class="revenue-card">
          <div class="rev-amount">¥{{ r.amount?.toLocaleString() || '0' }}</div>
          <div class="rev-meta"><span class="rev-source">{{ sourceLabel(r.source_type || r.channel) }}</span><span class="rev-date">{{ r.date?.slice(0, 10) || r.created_at?.slice(0, 10) }}</span></div>
        </div>
      </div>
    </div>

    <!-- Partners Tab -->
    <div v-if="activeTab === 'partners'" class="tab-content">
      <div class="toolbar">
        <select v-model="partnerFilter" class="filter-select" @change="loadPartners"><option value="">全部类型</option><option value="manufacturer">供应商/工厂</option><option value="pod_platform">POD平台</option><option value="client">授权方/客户</option></select>
        <button class="btn btn-primary" @click="showAddPartner = true">👥 添加伙伴</button>
      </div>
      <EmptyState v-if="partners.length === 0" icon="👥" title="暂无合作伙伴" description="添加工厂、供应商或客户信息" :show-action="true" :primary-action="{ label: '👥 添加伙伴', onClick: () => showAddPartner = true }" />
      <div v-else class="partner-grid">
        <div v-for="p in partners" :key="p.id" class="partner-card">
          <div class="partner-name">{{ p.name || p.company_name }}</div>
          <div class="partner-type">类型: {{ p.type || '-' }}</div>
          <div v-if="p.rating" class="partner-rating">⭐ {{ p.rating }}/5</div>
        </div>
      </div>
    </div>

    <!-- Orders Tab -->
    <div v-if="activeTab === 'orders'" class="tab-content">
      <div class="toolbar">
        <select v-model="orderFilter" class="filter-select" @change="loadOrders"><option value="">全部状态</option><option value="pending">待确认</option><option value="confirmed">已确认</option><option value="in_production">生产中</option><option value="shipped">已发货</option><option value="completed">已完成</option><option value="cancelled">已取消</option></select>
      </div>
      <EmptyState v-if="orders.length === 0" icon="📋" title="暂无订单记录" description="制造订单和POD订单将在这里汇总" />
      <div v-else class="order-list">
        <div v-for="o in orders" :key="o.id" class="order-card">
          <div class="order-header"><span class="order-number">{{ o.order_number }}</span><span :class="['status-badge', o.status]">{{ statusLabel(o.status) }}</span></div>
          <div class="order-body"><span>{{ o.product_name || '产品' }} × {{ o.quantity || 1 }}</span><span v-if="o.total_amount">¥{{ o.total_amount.toLocaleString() }}</span></div>
        </div>
      </div>
    </div>

    <!-- Notifications Tab -->
    <div v-if="activeTab === 'notifications'" class="tab-content">
      <div class="toolbar"><button class="btn btn-secondary" @click="store.markAllRead()">✅ 全部已读</button></div>
      <EmptyState v-if="notifications.length === 0" icon="🔔" title="暂无通知" description="存证完成、侵权扫描结果等通知将显示在这里" />
      <div v-else class="notif-list">
        <div v-for="n in notifications" :key="n.id" :class="['notif-item', { unread: !n.is_read }]" @click="store.markRead(n.id)">
          <div class="notif-title">{{ n.title }}</div><div class="notif-content">{{ n.content }}</div><div class="notif-time">{{ n.created_at?.slice(0, 16) }}</div>
        </div>
      </div>
    </div>

    <!-- Analytics Tab -->
    <div v-if="activeTab === 'analytics'" class="tab-content">
      <div class="analytics-period">
        <select v-model="analyticsPeriod" class="form-select form-select-sm" @change="loadAnalyticsSummary">
          <option value="month">本月</option>
          <option value="quarter">本季度</option>
          <option value="year">本年</option>
          <option value="all">全部</option>
        </select>
      </div>

      <!-- Summary cards -->
      <div class="analytics-summary" v-if="analyticsSummary.total_revenue !== undefined">
        <div class="a-stat"><div class="a-stat-value">¥{{ analyticsSummary.total_revenue?.toFixed(2) || '0' }}</div><div class="a-stat-label">总收入</div></div>
        <div class="a-stat"><div class="a-stat-value">{{ analyticsSummary.order_count || 0 }}</div><div class="a-stat-label">订单数</div></div>
        <div class="a-stat"><div class="a-stat-value">{{ analyticsSummary.avg_order_value?.toFixed(2) || '0' }}</div><div class="a-stat-label">客单价</div></div>
        <div class="a-stat"><div class="a-stat-value">{{ analyticsSummary.platform_count || 0 }}</div><div class="a-stat-label">活跃平台</div></div>
      </div>

      <!-- Charts -->
      <div class="charts-grid" v-if="analyticsRevenues.length">
        <div class="chart-card">
          <h3>📊 按来源类型</h3>
          <div ref="sourceChartRef" style="height:260px"></div>
        </div>
        <div class="chart-card">
          <h3>📈 月度趋势</h3>
          <div ref="monthChartRef" style="height:260px"></div>
        </div>
      </div>
      <EmptyState v-else icon="📊" title="暂无分析数据" description="收入数据将在此处生成可视化图表" />
    </div>

    <!-- Add Revenue Modal -->
    <div v-if="showAddRevenue" class="modal-overlay" @click.self="showAddRevenue = false">
      <div class="modal-card">
        <h3>登记收入</h3>
        <form @submit.prevent="submitRevenue">
          <label>金额 <input v-model="revForm.amount" type="number" step="0.01" required /></label>
          <label>来源类型 <select v-model="revForm.source_type" required><option value="commission">约稿</option><option value="pod">POD</option><option value="licensing">授权</option><option value="royalty">版税</option><option value="other">其他</option></select></label>
          <label>日期 <input v-model="revForm.date" type="date" required /></label>
          <label>备注 <input v-model="revForm.notes" /></label>
          <div class="modal-actions"><button type="button" class="btn btn-secondary" @click="showAddRevenue = false">取消</button><button type="submit" class="btn btn-primary">确认</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useBusinessStore } from '@/stores/useBusinessStore'
import type { RevenueRecord } from '@/types/business'
import EmptyState from '@/components/common/EmptyState.vue'
import * as echarts from 'echarts'

const store = useBusinessStore()
const revenues = computed(() => store.revenues)
const partners = computed(() => store.partners)
const orders = computed(() => store.orders)
const notifications = computed(() => store.notifications)
const loading = computed(() => store.loading)

const activeTab = ref('revenue')
const showAddRevenue = ref(false)
const showAddPartner = ref(false)
const partnerFilter = ref('')
const orderFilter = ref('')
const csvInputRef = ref<HTMLInputElement>()

// ─── Analytics ───
const analyticsPeriod = ref('month')
const sourceChartRef = ref<HTMLElement>()
const monthChartRef = ref<HTMLElement>()
let sourceChart: echarts.ECharts | null = null
let monthChart: echarts.ECharts | null = null

const analyticsRevenues = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  return revenues.value.filter((r: RevenueRecord) => {
    const d = new Date(r.date || r.created_at)
    if (analyticsPeriod.value === 'month') return d.getFullYear() === year && d.getMonth() === month
    if (analyticsPeriod.value === 'quarter') {
      const q = Math.floor(month / 3)
      const dq = Math.floor(d.getMonth() / 3)
      return d.getFullYear() === year && dq === q
    }
    if (analyticsPeriod.value === 'year') return d.getFullYear() === year
    return true
  })
})

const analyticsSummary = computed(() => {
  const revs = analyticsRevenues.value
  const total = revs.reduce((s: number, r: RevenueRecord) => s + (Number(r.amount) || 0), 0)
  const bySource: Record<string, number> = {}
  revs.forEach((r: RevenueRecord) => {
    const src = r.source_type || r.channel || 'other'
    bySource[src] = (bySource[src] || 0) + (Number(r.amount) || 0)
  })
  const platformCount = new Set(revs.map((r: RevenueRecord) => r.source_type || r.channel)).size
  return {
    total_revenue: total,
    order_count: revs.length,
    avg_order_value: revs.length ? total / revs.length : 0,
    platform_count: platformCount,
    by_source: bySource,
  }
})

function renderCharts() {
  // Source pie chart
  if (sourceChartRef.value) {
    if (sourceChart) sourceChart.dispose()
    sourceChart = echarts.init(sourceChartRef.value)
    const sourceLabels: Record<string, string> = { commission: '约稿', pod: 'POD', licensing: '授权', royalty: '版税', other: '其他' }
    sourceChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['45%', '75%'],
        itemStyle: { borderRadius: 8, borderColor: 'oklch(100% 0 0)', borderWidth: 2 },
        data: Object.entries(analyticsSummary.value.by_source || {}).map(([name, value]) => ({
          name: sourceLabels[name] || name, value,
        })),
        label: { show: true, formatter: '{b}\n¥{c}' },
      }],
    })
  }
  // Monthly bar chart
  if (monthChartRef.value) {
    if (monthChart) monthChart.dispose()
    monthChart = echarts.init(monthChartRef.value)
    const byMonth: Record<string, number> = {}
    analyticsRevenues.value.forEach((r: RevenueRecord) => {
      const m = (r.date || r.created_at || '').slice(0, 7)
      if (m) byMonth[m] = (byMonth[m] || 0) + (Number(r.amount) || 0)
    })
    const months = Object.keys(byMonth).sort()
    monthChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: months, axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
      series: [{
        type: 'bar',
        data: months.map(m => byMonth[m]),
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'oklch(56% 0.12 170)' },
            { offset: 1, color: 'oklch(62% 0.16 260)' },
          ]),
        },
      }],
      grid: { top: 10, right: 10, bottom: 20, left: 50 },
    })
  }
}

watch(() => analyticsRevenues.value.length, async () => {
  await nextTick()
  renderCharts()
}, { immediate: true })

onMounted(async () => {
  await Promise.all([store.fetchRevenues(), store.fetchPartners(), store.fetchOrders(), store.fetchNotifications(), store.fetchUnreadCount(), store.fetchDashboard()])
  window.addEventListener('resize', () => {
    sourceChart?.resize()
    monthChart?.resize()
  })
})

async function loadAnalyticsSummary() {
  await store.fetchRevenueSummary({ period: analyticsPeriod.value })
}

const tabs = [
  { key: 'revenue', label: '收入', icon: '💰' },
  { key: 'partners', label: '合作伙伴', icon: '👥' },
  { key: 'orders', label: '订单', icon: '📦' },
  { key: 'notifications', label: '通知', icon: '🔔', badge: store.unreadCount > 0 ? store.unreadCount : 0 },
  { key: 'analytics', label: '分析', icon: '📊' },
]

const revForm = reactive({ amount: '', source_type: 'commission', date: new Date().toISOString().slice(0, 10), notes: '' })

const stats = computed(() => ({
  totalRevenue: store.revenues.reduce((s: number, r: RevenueRecord) => s + (Number(r.amount) || 0), 0),
  monthlyRevenue: store.revenues.filter((r: RevenueRecord) => (r.date || r.created_at || '').slice(0, 7) === new Date().toISOString().slice(0, 7)).reduce((s: number, r: RevenueRecord) => s + (Number(r.amount) || 0), 0),
  productCount: 0,
  partnerCount: store.partners.length,
}))

const sourceLabels: Record<string, string> = { commission: '约稿', pod: 'POD', licensing: '授权', royalty: '版税', other: '其他' }
const statusLabels: Record<string, string> = { pending: '待确认', confirmed: '已确认', in_production: '生产中', shipped: '已发货', completed: '已完成', cancelled: '已取消' }
function sourceLabel(type?: string) { return sourceLabels[type || ''] || type || '-' }
function statusLabel(status?: string) { return statusLabels[status || ''] || status || '-' }
function loadPartners() { store.fetchPartners(partnerFilter.value ? { type: partnerFilter.value } : undefined) }
function loadOrders() { store.fetchOrders(orderFilter.value ? { status: orderFilter.value } : undefined) }
async function submitRevenue() { await store.addRevenue({ ...revForm, amount: parseFloat(revForm.amount) }); showAddRevenue.value = false; revForm.amount = ''; revForm.notes = '' }
function triggerCsvImport() { csvInputRef.value?.click() }
async function handleCsvImport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]; if (!file) return
  const fd = new FormData(); fd.append('file', file)
  try { const res = await store.importCsv(fd); (window as any).$toast?.show?.('success', `导入完成: ${res.data?.imported || 0} 条`) } catch { (window as any).$toast?.show?.('error', 'CSV 导入失败') }
}

</script>

<style scoped>
.business-view { max-width: 1200px; }
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--surface); border-radius: var(--radius); padding: 20px; text-align: center; border: 1px solid var(--border); }
.stat-icon { font-size: 1.8rem; margin-bottom: 8px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.tab-bar { display: flex; gap: 4px; border-bottom: 2px solid var(--border); margin-bottom: 20px; padding-bottom: 0; }
.tab-btn { padding: 10px 20px; border: none; background: none; cursor: pointer; font-size: 0.9rem; color: var(--muted); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
.tab-btn:hover { color: var(--fg); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab-badge { background: var(--orange); color: #fff; border-radius: 100px; padding: 1px 7px; font-size: 0.7rem; }
.toolbar { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
.filter-select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); font-size: 0.85rem; }
.btn { padding: 8px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border); font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-secondary { background: var(--surface); color: var(--fg); }
.tab-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.revenue-list, .order-list, .notif-list { display: flex; flex-direction: column; gap: 8px; }
.revenue-card, .order-card, .partner-card, .notif-item { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; }
.rev-amount { font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.rev-meta { display: flex; gap: 12px; font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.partner-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.partner-name { font-weight: 600; font-size: 1rem; }
.partner-type { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.order-header { display: flex; justify-content: space-between; align-items: center; }
.order-number { font-weight: 600; }
.order-body { display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.9rem; }
.status-badge { padding: 2px 10px; border-radius: 100px; font-size: 0.75rem; font-weight: 600; }
.status-badge.completed { background: #e6f7ed; color: #1a7d36; }
.status-badge.pending, .status-badge.confirmed { background: #fff8e1; color: #b8860b; }
.status-badge.cancelled { background: #fde8e8; color: #c62828; }
.notif-item { cursor: pointer; transition: background 0.15s; }
.notif-item:hover { background: oklch(56% 0.12 170 / 0.04); }
.notif-item.unread { border-left: 3px solid var(--accent); }
.notif-title { font-weight: 600; font-size: 0.9rem; }
.notif-content { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.notif-time { font-size: 0.72rem; color: var(--muted); margin-top: 6px; }
.modal-overlay { position: fixed; inset: 0; background: oklch(0 0 0 / 0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-card { background: var(--surface); border-radius: var(--radius); padding: 24px; max-width: 420px; width: 90%; box-shadow: 0 8px 32px oklch(0 0 0 / 0.12); }
.modal-card h3 { margin-bottom: 16px; }
.modal-card label { display: block; margin-bottom: 12px; font-size: 0.85rem; }
.modal-card input, .modal-card select { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); font-size: 0.9rem; margin-top: 4px; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
@media (max-width: 767px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
.analytics-period { display: flex; justify-content: flex-end; margin-bottom: 16px; }
.form-select-sm { padding: 6px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); font-size: 0.82rem; }
.analytics-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.a-stat { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px; text-align: center; }
.a-stat-value { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
.a-stat-label { font-size: 0.78rem; color: var(--muted); margin-top: 4px; }
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px; }
.chart-card h3 { margin: 0 0 12px; font-size: 0.92rem; color: var(--fg); }
</style>
