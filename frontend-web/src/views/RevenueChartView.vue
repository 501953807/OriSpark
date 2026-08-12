<template>
  <div class="revenue-chart-view">
    <div class="view-header">
      <h2>收入分析</h2>
      <div class="header-actions">
        <select v-model="months" class="period-select" @change="loadData">
          <option :value="3">近 3 个月</option>
          <option :value="6">近 6 个月</option>
          <option :value="12" selected>近 12 个月</option>
        </select>
        <div class="export-group">
          <button class="btn btn-secondary" @click="exportData('csv')">导出 CSV</button>
          <button class="btn btn-secondary" @click="exportData('json')">导出 JSON</button>
        </div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">¥{{ summary?.total_revenue?.toLocaleString() || '0' }}</div>
        <div class="stat-label">总收入</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ summary?.months || 0 }}</div>
        <div class="stat-label">统计月份</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ (diversity?.diversity_index ?? 0).toFixed(2) }}</div>
        <div class="stat-label">多元化指数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ diversity?.total_sources || 0 }}</div>
        <div class="stat-label">收入来源</div>
      </div>
    </div>

    <div class="diversity-alerts" v-if="diversity?.warnings?.length">
      <div v-for="(w, i) in diversity.warnings" :key="i" class="alert-item">{{ w }}</div>
    </div>

    <div class="chart-grid">
      <div class="chart-card">
        <h3>月度收入趋势</h3>
        <div ref="barChartRef" class="chart-container" />
      </div>
      <div class="chart-card">
        <h3>收入来源分布</h3>
        <div ref="pieChartRef" class="chart-container" />
      </div>
    </div>

    <div class="records-table" v-if="records.length">
      <h3>收入明细</h3>
      <table>
        <thead>
          <tr>
            <th>日期</th><th>类别</th><th>金额</th><th>币种</th><th>平台</th><th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.id">
            <td>{{ r.date }}</td>
            <td>{{ categoryLabel(r.category) }}</td>
            <td class="amount">¥{{ r.amount?.toLocaleString() }}</td>
            <td>{{ r.currency }}</td>
            <td>{{ r.platform || '-' }}</td>
            <td class="desc">{{ r.description || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { revenueApi } from '@/api/revenue'
import client from '@/api/client'
import { useAuthStore } from '@/stores/useAuthStore'

const authStore = useAuthStore()
const userId = authStore.user?.id || ''

const months = ref(12)
const summary = ref<any>(null)
const diversity = ref<any>(null)
const records = ref<any[]>([])
const barChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let barChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

const CATEGORY_NAMES: Record<string, string> = {
  ad_revenue: '广告分成',
  sponsorship: '品牌赞助',
  subscription: '付费订阅',
  tip: '打赏',
  ecommerce: '电商',
  affiliate: '联盟营销',
  knowledge_payment: '知识付费',
  ip_licensing: 'IP 授权',
}

function categoryLabel(cat: string) {
  return CATEGORY_NAMES[cat] || cat
}

async function loadData() {
  if (!userId) return
  try {
    const [sumRes, divRes] = await Promise.all([
      revenueApi.getSummary(userId, months.value),
      revenueApi.getDiversity(userId, months.value),
    ])
    summary.value = sumRes.data
    diversity.value = divRes.data
    renderCharts()
  } catch (e) {
    console.error('load revenue data failed:', e)
  }
}

async function loadRecords() {
  try {
    const resp = await client.get('/revenue/records/export', {
      params: { format: 'json' },
    })
    records.value = resp.data.data || []
  } catch (e) {
    console.error('load records failed:', e)
  }
}

function renderCharts() {
  if (!summary.value) return
  const trend = summary.value.monthly_trend || []

  if (barChartRef.value) {
    if (!barChart) barChart = echarts.init(barChartRef.value)
    barChart.setOption({
      tooltip: { trigger: 'axis', formatter: (p: any) => `¥${p[0]?.value?.toLocaleString() || 0}` },
      grid: { left: 60, right: 20, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: trend.map((t: any) => t.month), axisLabel: { color: 'oklch(0.5 0.02 264)', fontSize: 11 } },
      yAxis: { type: 'value', axisLabel: { color: 'oklch(0.5 0.02 264)', formatter: (v: number) => `¥${v}` }, splitLine: { lineStyle: { color: 'oklch(0.95 0 0)' } } },
      series: [{ type: 'bar', data: trend.map((t: any) => t.amount), itemStyle: { color: 'oklch(0.55 0.02 264)', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 40 }],
    })
  }

  if (pieChartRef.value && diversity.value?.category_distribution) {
    if (!pieChart) pieChart = echarts.init(pieChartRef.value)
    const dist = diversity.value.category_distribution
    const pieData = Object.entries(dist).map(([key, v]: [string, any]) => ({
      name: CATEGORY_NAMES[key] || key,
      value: v.amount,
    }))
    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
        itemStyle: { borderRadius: 6, borderColor: 'oklch(100% 0 0)', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n¥{c}', fontSize: 11 },
        data: pieData,
      }],
    })
  }
}

async function exportData(format: 'csv' | 'json') {
  try {
    const resp = await client.get('/revenue/records/export', {
      params: { format },
      responseType: format === 'csv' ? 'blob' : 'json',
    })
    const blob = new Blob([resp.data], { type: format === 'csv' ? 'text/csv;charset=utf-8;' : 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `revenue_export.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('export failed:', e)
  }
}

watch(months, () => { loadData(); loadRecords() })

onMounted(() => { loadData(); loadRecords() })
</script>

<style scoped>
.revenue-chart-view { padding: 24px; max-width: 1200px; margin: 0 auto; }
.view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.view-header h2 { margin: 0; font-size: 22px; color: oklch(0.25 0.02 264); }
.header-actions { display: flex; gap: 12px; align-items: center; }
.period-select { padding: 6px 12px; border: 1px solid oklch(0.88 0.01 264); border-radius: 8px; font-size: 13px; color: oklch(0.35 0.02 264); background: oklch(1 0 0); }
.export-group { display: flex; gap: 8px; }
.btn { padding: 6px 14px; border-radius: 8px; font-size: 13px; cursor: pointer; border: none; font-weight: 600; }
.btn-secondary { background: oklch(0.92 0.01 264); color: oklch(0.35 0.02 264); }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: oklch(1 0 0); border: 1px solid oklch(0.92 0.01 264); border-radius: 12px; padding: 20px; text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; color: oklch(0.35 0.02 264); }
.stat-label { font-size: 12px; color: oklch(0.55 0.02 264); margin-top: 4px; }
.diversity-alerts { display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; }
.alert-item { padding: 10px 16px; border-radius: 8px; font-size: 13px; background: oklch(0.96 0.01 264); color: oklch(0.4 0.02 264); }
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.chart-card { background: oklch(1 0 0); border: 1px solid oklch(0.92 0.01 264); border-radius: 12px; padding: 20px; }
.chart-card h3 { margin: 0 0 16px 0; font-size: 15px; color: oklch(0.35 0.02 264); }
.chart-container { height: 280px; }
.records-table { background: oklch(1 0 0); border: 1px solid oklch(0.92 0.01 264); border-radius: 12px; padding: 20px; }
.records-table h3 { margin: 0 0 16px 0; font-size: 15px; color: oklch(0.35 0.02 264); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th { text-align: left; padding: 8px 12px; color: oklch(0.5 0.02 264); border-bottom: 2px solid oklch(0.92 0.01 264); font-weight: 600; }
tbody td { padding: 10px 12px; border-bottom: 1px solid oklch(0.96 0 0); color: oklch(0.35 0.02 264); }
tbody tr:hover { background: oklch(0.98 0.005 264); }
.amount { font-weight: 600; color: oklch(0.4 0.02 264); }
.desc { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .chart-grid { grid-template-columns: 1fr; }
}
</style>
