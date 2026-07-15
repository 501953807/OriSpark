<template>
  <div class="dashboard-view">
    <!-- Stats row -->
    <div class="stats-row">
      <StatCard icon="🎨" label="作品总数" :value="stats?.total_works ?? 0" to="/app/works" color="green" />
      <StatCard icon="🔒" label="已存证" :value="stats?.total_notarized ?? 0" to="/app/notary" color="purple" />
      <StatCard icon="🛡️" label="侵权告警" :value="stats?.infringement_alerts ?? 0" to="/app/monitor" color="orange" />
      <StatCard icon="💰" label="本月收入" :value="`¥${fmtMoney(stats?.monthly_revenue ?? 0)}`" color="blue" />
    </div>

    <!-- Business Overview -->
    <div class="card business-overview">
      <h3 class="section-title">📊 经营概览</h3>
      <div class="overview-grid">
        <div class="overview-item">
          <span class="overview-label">总收入</span>
          <span class="overview-value">¥{{ fmtMoney(overview.total_revenue) }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">活跃产品</span>
          <span class="overview-value">{{ overview.active_products }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">进行中活动</span>
          <span class="overview-value">{{ overview.active_campaigns }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">待处理订单</span>
          <span class="overview-value">{{ overview.pending_orders }}</span>
        </div>
      </div>
    </div>

    <!-- Analytics Charts -->
    <div class="charts-section">
      <div class="chart-card card">
        <div class="chart-header">
          <h3 class="chart-title">收入趋势</h3>
          <span class="chart-subtitle">最近 12 个月</span>
        </div>
        <RevenueChart :data="dashboardStore.revenue" />
      </div>

      <div class="chart-card card">
        <div class="chart-header">
          <h3 class="chart-title">作品创建趋势</h3>
          <span class="chart-subtitle">
            最近 30 天 · 平均 {{ dashboardStore.trends?.avg_daily ?? 0 }}/日
          </span>
        </div>
        <TrendChart :data="dashboardStore.trends" />
      </div>
    </div>

    <!-- Quick modules -->
    <div class="section-title">快捷模块</div>
    <div class="quick-modules">
      <div v-for="mod in modules" :key="mod.path" class="module-tile card" @click="$router.push(mod.path)">
        <div class="module-icon">{{ mod.icon }}</div>
        <div class="module-name">{{ mod.name }}</div>
        <div class="module-desc">{{ mod.desc }}</div>
      </div>
    </div>

    <!-- Two-column panels -->
    <div class="panels-row">
      <div class="panel card">
        <div class="panel-header">
          <h3 class="panel-title">最近作品</h3>
          <router-link to="/app/works" class="panel-link">查看全部 →</router-link>
        </div>
        <div class="panel-body">
          <div v-if="dashboardStore.loading" class="panel-empty"><LoadingSpinner text="加载中..." /></div>
          <div v-else-if="recentWorks.length === 0" class="panel-empty">还没有导入作品</div>
          <div v-for="work in recentWorks" :key="work.id" class="work-row" @click="$router.push(`/app/works/${work.id}`)">
            <div class="work-thumb">
              <LazyImage v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
              <span v-else class="work-thumb-placeholder">{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
            </div>
            <div class="work-info">
              <div class="work-name">{{ work.title }}</div>
              <div class="work-meta">{{ work.file_type }} · {{ work.imported_at?.slice(0, 10) }}</div>
            </div>
            <StatusBadge :status="work.is_verified ? 'confirmed' : 'draft'" :labels="{ confirmed: '已存证', draft: '待存证' }" :variants="{ confirmed: 'success', draft: 'info' }" />
          </div>
        </div>
      </div>

      <div class="panel card">
        <div class="panel-header">
          <h3 class="panel-title">侵权告警</h3>
          <router-link to="/app/monitor" class="panel-link">查看全部 →</router-link>
        </div>
        <div class="panel-body">
          <div v-if="dashboardStore.loading" class="panel-empty"><LoadingSpinner text="加载中..." /></div>
          <div v-else-if="(stats?.infringement_alerts ?? 0) === 0" class="panel-empty">暂无告警</div>
          <div v-for="alert in (stats?.recent_alerts || [])" :key="alert.id" class="work-row" @click="$router.push('/app/monitor')">
            <div class="work-thumb">
              <span class="work-thumb-placeholder">⚠️</span>
            </div>
            <div class="work-info">
              <div class="work-name">{{ alert.work_title || '未知作品' }}</div>
              <div class="work-meta">{{ alert.matched_title || '疑似侵权' }} · {{ alert.found_at?.slice(0, 10) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import LazyImage from '@/components/common/LazyImage.vue'
import RevenueChart from '@/components/dashboard/RevenueChart.vue'
import TrendChart from '@/components/dashboard/TrendChart.vue'
import { useDashboardStore } from '@/stores/useDashboardStore'
import { storeToRefs } from 'pinia'

const dashboardStore = useDashboardStore()
const { stats, recentWorks } = storeToRefs(dashboardStore)

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}

const modules = [
  { path: '/app/works', icon: '🎨', name: '作品管理', desc: '导入、分类、搜索你的创作作品' },
  { path: '/app/projects', icon: '📁', name: '项目分组', desc: '按项目组织你的作品' },
  { path: '/app/notary', icon: '🔒', name: '存证确权', desc: '区块链存证，保护你的版权' },
  { path: '/app/monitor', icon: '🛡️', name: '侵权监测', desc: '自动扫描，发现侵权行为' },
  { path: '/app/ipr', icon: '📋', name: 'IP 登记', desc: '商标/版权/专利申请指引' },
  { path: '/app/supply', icon: '🏭', name: '供应链', desc: '管理工厂合作与订单' },
  { path: '/app/publish', icon: '🚀', name: '发布变现', desc: '一键发布，多渠道销售' },
  { path: '/app/business', icon: '💼', name: '经营管理', desc: '收入、订单、合作伙伴概览' },
]

const overview = reactive({
  total_revenue: 0,
  active_products: 0,
  active_campaigns: 0,
  pending_orders: 0,
})

function fmtMoney(n: number): string {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

onMounted(async () => {
  try {
    await dashboardStore.refreshAll()
    // Load business overview from supply dashboard API
    try {
      const { supplyApi } = await import('@/api/supply')
      const r = await supplyApi.dashboard()
      const d = r.data?.data || {}
      const s = d.summary || {}
      overview.total_revenue = s.total_revenue || 0
      overview.active_products = s.total_products || 0
      overview.active_campaigns = s.active_campaigns || 0
      overview.pending_orders = s.total_orders || 0
    } catch {
      // Silently continue if supply API unavailable
    }
  } catch {
    ;(window as any).$toast?.show('加载仪表盘数据失败', 'error')
  }
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
@media (max-width: 1024px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .stats-row { grid-template-columns: 1fr; } }
.section-title {
  font-size: 1rem;
  font-weight: 700;
  font-family: var(--font-display);
}
.quick-modules {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}
@media (max-width: 1200px) { .quick-modules { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px) { .quick-modules { grid-template-columns: repeat(2, 1fr); } }
.module-tile {
  padding: 20px;
  cursor: pointer;
}
.module-icon { font-size: 1.8rem; margin-bottom: 8px; }
.module-name { font-size: 0.9rem; font-weight: 700; }
.module-desc { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }

/* Business Overview */
.business-overview { padding: 16px 20px; }
.business-overview .section-title { font-size: 0.85rem; margin-bottom: 12px; }
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 768px) { .overview-grid { grid-template-columns: repeat(2, 1fr); } }
.overview-item {
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.overview-label { font-size: 0.75rem; color: var(--muted); }
.overview-value { font-size: 1.1rem; font-weight: 700; margin-top: 4px; }

/* Analytics Charts */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 1024px) { .charts-section { grid-template-columns: 1fr; } }
.chart-card {
  overflow: hidden;
}
.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 18px 20px 8px;
  border-bottom: 1px solid var(--border);
}
.chart-title {
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}
.chart-subtitle {
  font-size: 0.75rem;
  color: var(--muted);
}

/* Panels */
.panels-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 1024px) { .panels-row { grid-template-columns: 1fr; } }
.panel { overflow: hidden; }
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}
.panel-title { font-size: 0.95rem; font-weight: 700; margin: 0; }
.panel-tabs { display: flex; gap: 4px; }
.panel-tab {
  padding: 4px 12px; border-radius: 100px; border: none; cursor: pointer;
  font-size: 0.78rem; font-weight: 600; background: transparent;
  color: var(--muted); transition: all 0.2s; font-family: var(--font-body);
}
.panel-tab.active { background: var(--accent); color: #fff; }
.panel-link { font-size: 0.82rem; color: var(--accent); font-weight: 600; text-decoration: none; }
.panel-body { padding: 12px 20px; }
.panel-empty { padding: 32px; text-align: center; color: var(--muted); font-size: 0.88rem; }
.work-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid oklch(93% 0.003 240);
  cursor: pointer;
  transition: background 0.15s;
}
.work-row:last-child { border-bottom: none; }
.work-row:hover { background: oklch(97% 0.002 240); margin: 0 -8px; padding: 10px 8px; border-radius: var(--radius-sm); }
.work-thumb {
  width: 40px; height: 40px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: oklch(95% 0.003 240);
  display: flex;
  align-items: center;
  justify-content: center;
}
.work-thumb img { width: 100%; height: 100%; object-fit: cover; }
.work-thumb-placeholder { font-size: 1.2rem; }
.work-info { flex: 1; min-width: 0; }
.work-name { font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.work-meta { font-size: 0.72rem; color: var(--muted); }
</style>
