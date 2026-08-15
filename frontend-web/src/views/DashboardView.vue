<template>
  <div class="dashboard-view" :class="{ 'dashboard-view--loading': dashboardStore.loading }">
    <div v-if="dashboardStore.loading" class="page-loading-overlay">
      <LoadingSpinner full-screen text="正在加载数据..." />
    </div>

    <!-- Page Title -->
    <div class="m-page-header">
      <h1 class="m-page-title">工作台</h1>
      <p class="m-page-subtitle">创作者全链路助手 · 数据概览</p>
    </div>

    <!-- Stats row (only for creator role) -->
    <div v-if="isCreatorRole" class="stats-row">
      <StatCard icon="🎨" label="作品总数" :value="stats?.total_works ?? 0" to="/app/works" color="green" />
      <StatCard icon="🔒" label="已存证" :value="stats?.total_notarized ?? 0" to="/app/notary" color="purple" />
      <StatCard icon="🛡️" label="侵权告警" :value="stats?.infringement_alerts ?? 0" to="/app/monitor" color="orange" />
      <StatCard icon="💰" label="本月收入" :value="`¥${fmtMoney(stats?.monthly_revenue ?? 0)}`" color="blue" />
    </div>

    <!-- Role-specific stats (non-creator) -->
    <div v-else class="stats-row">
      <StatCard icon="📝" label="关联合约" :value="stats?.total_works ?? 0" to="/app/contract-market" color="blue" />
      <StatCard icon="🤝" label="进行中交易" :value="stats?.infringement_alerts ?? 0" to="/app/contract-market" color="green" />
      <StatCard icon="⚠️" label="风险预警" :value="0" to="/app/risk-warning" color="orange" />
      <StatCard icon="💰" label="本月收益" :value="`¥${fmtMoney(stats?.monthly_revenue ?? 0)}`" color="blue" />
    </div>

    <!-- Business Overview -->
    <MCard title="📊 经营概览">
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
    </MCard>

    <!-- Analytics Charts -->
    <div class="charts-section">
      <MCard title="收入趋势" subtitle="最近 12 个月">
        <RevenueChart :data="dashboardStore.revenue" />
      </MCard>
      <MCard title="作品创建趋势" :subtitle="`最近 30 天 · 平均 ${dashboardStore.trends?.avg_daily ?? 0}/日`">
        <TrendChart :data="dashboardStore.trends" />
      </MCard>
    </div>

    <!-- Quick modules -->
    <MCard title="快捷模块">
      <div class="quick-modules">
        <div v-for="mod in modules" :key="mod.path" class="module-tile" @click="$router.push(mod.path)">
          <div class="module-icon">{{ mod.icon }}</div>
          <div class="module-name">{{ mod.name }}</div>
          <div class="module-desc">{{ mod.desc }}</div>
        </div>
      </div>
    </MCard>

    <!-- Two-column panels (only for creator role) -->
    <div v-if="isCreatorRole" class="panels-row">
      <MCard title="最近作品">
        <template #actions>
          <router-link to="/app/works" class="m-link">查看全部 →</router-link>
        </template>
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
      </MCard>

      <MCard title="侵权告警">
        <template #actions>
          <router-link to="/app/monitor" class="m-link">查看全部 →</router-link>
        </template>
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
      </MCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, computed } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import LazyImage from '@/components/common/LazyImage.vue'
import RevenueChart from '@/components/dashboard/RevenueChart.vue'
import TrendChart from '@/components/dashboard/TrendChart.vue'
import MCard from '@/components/ui/MCard.vue'
import { useDashboardStore } from '@/stores/useDashboardStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { storeToRefs } from 'pinia'
import { PARTICIPANT_ROLES } from '@/types/roles'

const dashboardStore = useDashboardStore()
const authStore = useAuthStore()
const { stats, recentWorks } = storeToRefs(dashboardStore)

const currentRole = computed(() => {
  const roles = authStore.participantRoles
  if (roles.length > 0) return roles[0]
  return 'creator'
})

const isCreatorRole = computed(() => currentRole.value === 'creator')

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}

const roleModules: Record<string, Array<{ path: string; icon: string; name: string; desc: string }>> = {
  creator: [
    { path: '/app/works', icon: '🎨', name: '作品管理', desc: '导入、分类、搜索你的创作作品' },
    { path: '/app/projects', icon: '📁', name: '项目分组', desc: '按项目组织你的作品' },
    { path: '/app/notary', icon: '🔒', name: '存证确权', desc: '区块链存证，保护你的版权' },
    { path: '/app/monitor', icon: '🛡️', name: '侵权监测', desc: '自动扫描，发现侵权行为' },
    { path: '/app/ipr', icon: '📋', name: 'IP 登记', desc: '商标/版权/专利申请指引' },
    { path: '/app/supply', icon: '🏭', name: '供应链', desc: '管理工厂合作与订单' },
    { path: '/app/publish', icon: '🚀', name: '发布变现', desc: '一键发布，多渠道销售' },
    { path: '/app/business', icon: '💼', name: '经营管理', desc: '收入、订单、合作伙伴概览' },
  ],
  operator: [
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '浏览和参与版权交易合约' },
    { path: '/app/multimarket', icon: '🌍', name: '多市场扩展', desc: '多渠道分发与推广' },
    { path: '/app/negotiation', icon: '🤝', name: '交易谈判', desc: '与版权方协商合作条款' },
    { path: '/app/capability', icon: '🧠', name: '能力评估', desc: '评估版权方创作能力' },
    { path: '/app/credit-improvement', icon: '💳', name: '信用提升', desc: '提升商业信用评级' },
    { path: '/app/business', icon: '💼', name: '经营管理', desc: '运营数据与收益分析' },
  ],
  legal_rep: [
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '审查合约条款与风险' },
    { path: '/app/contract-risk', icon: '📋', name: '合同风险评估', desc: '评估合约法律风险' },
    { path: '/app/negotiation', icon: '🤝', name: '交易谈判', desc: '参与合约条款协商' },
    { path: '/app/risk-center', icon: '🔔', name: '风控中心', desc: '监控法律风险事件' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  tax_agent: [
    { path: '/app/tax-settlement', icon: '💱', name: '税务结算', desc: '处理跨国税务申报' },
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '查看关联合约税务信息' },
    { path: '/app/risk-warning', icon: '⚠️', name: '风险预警', desc: '税务合规风险提示' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  logistics: [
    { path: '/app/supply', icon: '🏭', name: '供应链管理', desc: '管理物流订单与配送' },
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '查看关联合约物流信息' },
    { path: '/app/risk-warning', icon: '⚠️', name: '风险预警', desc: '物流状态异常提醒' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  insurer: [
    { path: '/app/insurance', icon: '🛡️', name: '保险市场', desc: '管理版权与履约保险' },
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '查看关联合约保险信息' },
    { path: '/app/risk-warning', icon: '⚠️', name: '风险预警', desc: '风险评估与理赔提醒' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  trader: [
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '浏览和订阅版权合约' },
    { path: '/app/marketplace', icon: '🤝', name: '商业撮合', desc: '发现匹配的版权方' },
    { path: '/app/multimarket', icon: '🌍', name: '多市场扩展', desc: '多渠道版权采购' },
    { path: '/app/capability', icon: '🧠', name: '能力评估', desc: '评估版权方创作能力' },
    { path: '/app/credit-improvement', icon: '💳', name: '信用提升', desc: '提升采购信用评级' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  payment_provider: [
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '管理合约支付托管' },
    { path: '/app/business', icon: '💼', name: '经营管理', desc: '查看交易结算数据' },
    { path: '/app/risk-warning', icon: '⚠️', name: '风险预警', desc: '支付风险监控' },
    { path: '/app/settings', icon: '⚙️', name: '偏好设置', desc: '系统配置与管理' },
  ],
  platform: [
    { path: '/app', icon: '📊', name: '工作台', desc: '平台运营总览' },
    { path: '/app/contract-market', icon: '📝', name: '合约市场', desc: '管理所有交易合约' },
    { path: '/app/marketplace', icon: '🤝', name: '商业撮合', desc: '撮合交易管理' },
    { path: '/app/supply', icon: '🏭', name: '供应链管理', desc: '管理供应链网络' },
    { path: '/app/insurance', icon: '🛡️', name: '保险市场', desc: '管理保险产品' },
    { path: '/app/risk-center', icon: '🔔', name: '风控中心', desc: '平台风险监控' },
    { path: '/app/enforcement-dashboard', icon: '⚖️', name: '维权流水线', desc: '维权案件管理' },
    { path: '/app/settings', icon: '⚙️', name: '系统设置', desc: '平台全局配置' },
  ],
}

const modules = computed(() => roleModules[currentRole.value] || roleModules['creator'])

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
  const loadDashboard = dashboardStore.refreshAll()
  const loadSupply = (async () => {
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
  })()
  try {
    await Promise.all([loadDashboard, loadSupply])
  } catch {
    ;(window as any).$toast?.show('加载仪表盘数据失败', 'error')
  }
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: var(--m-space-6);
}

/* ── Page Header ── */
.m-page-header { margin-bottom: 0; }
.m-page-title {
  font-size: var(--m-font-size-xl);
  font-weight: var(--m-font-weight-bold);
  color: var(--m-on-surface);
  margin: 0 0 4px;
}
.m-page-subtitle {
  font-size: var(--m-font-size-sm);
  color: var(--m-grey-500);
  margin: 0;
}

/* ── Stats Row ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--m-space-4);
}
@media (max-width: 1024px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .stats-row { grid-template-columns: 1fr; } }

/* ── Overview Grid ── */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--m-space-3);
}
@media (max-width: 768px) { .overview-grid { grid-template-columns: repeat(2, 1fr); } }
.overview-item {
  display: flex;
  flex-direction: column;
  padding: var(--m-space-3);
  background: var(--m-bg-subtle);
  border-radius: var(--m-radius-sm);
}
.overview-label { font-size: var(--m-font-size-xs); color: var(--m-grey-500); }
.overview-value { font-size: var(--m-font-size-lg); font-weight: var(--m-font-weight-bold); margin-top: 4px; color: var(--m-on-surface); }

/* ── Charts ── */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--m-space-5);
}
@media (max-width: 1024px) { .charts-section { grid-template-columns: 1fr; } }

/* ── Quick Modules ── */
.quick-modules {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--m-space-3);
}
@media (max-width: 1200px) { .quick-modules { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px) { .quick-modules { grid-template-columns: repeat(2, 1fr); } }
.module-tile {
  padding: var(--m-space-4);
  cursor: pointer;
  border-radius: var(--m-radius-md);
  transition: background var(--m-transition-fast);
}
.module-tile:hover { background: var(--m-bg-subtle); }
.module-icon { font-size: 1.8rem; margin-bottom: 8px; }
.module-name { font-size: var(--m-font-size-sm); font-weight: var(--m-font-weight-semibold); color: var(--m-on-surface); }
.module-desc { font-size: var(--m-font-size-xs); color: var(--m-grey-500); margin-top: 4px; }

/* ── Panels ── */
.panels-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--m-space-5);
}
@media (max-width: 1024px) { .panels-row { grid-template-columns: 1fr; } }
.panel-body { padding: var(--m-space-3) 0; }
.panel-empty { padding: var(--m-space-8); text-align: center; color: var(--m-grey-400); font-size: var(--m-font-size-sm); }
.work-row {
  display: flex;
  align-items: center;
  gap: var(--m-space-3);
  padding: var(--m-space-2) 0;
  cursor: pointer;
  transition: background var(--m-transition-fast);
}
.work-row:hover { background: var(--m-bg-subtle); margin: 0 calc(-1 * var(--m-space-3)); padding: var(--m-space-2) var(--m-space-3); border-radius: var(--m-radius-sm); }
.work-thumb {
  width: 40px; height: 40px;
  border-radius: var(--m-radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--m-surface-2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.work-thumb img { width: 100%; height: 100%; object-fit: cover; }
.work-thumb-placeholder { font-size: 1.2rem; }
.work-info { flex: 1; min-width: 0; }
.work-name { font-size: var(--m-font-size-sm); font-weight: var(--m-font-weight-medium); color: var(--m-on-surface); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.work-meta { font-size: var(--m-font-size-xs); color: var(--m-grey-500); }

/* ── Link ── */
.m-link { font-size: var(--m-font-size-sm); color: rgb(85, 133, 255); text-decoration: none; font-weight: var(--m-font-weight-medium); }
.m-link:hover { text-decoration: underline; }

/* ── Loading Overlay ── */
.dashboard-view--loading {
  position: relative;
  pointer-events: none;
  user-select: none;
}
.dashboard-view--loading > *:not(.page-loading-overlay) {
  opacity: 0.3;
  filter: blur(2px);
  transition: opacity 0.3s, filter 0.3s;
}
.page-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--m-bg);
}
</style>
