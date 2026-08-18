<template>
  <div v-if="activeTab === 'dashboard'" class="dashboard animate-fade-in">
    <div class="actions-bar">
      <div class="filter-group">
        <select :value="dashFilterType" class="form-input" @change="$emit('update:dashFilterType', ($event.target as HTMLSelectElement).value); $emit('load-portfolio')">
          <option value="">全部类型</option>
          <option value="copyright">著作权</option>
          <option value="trademark">商标</option>
          <option value="design_patent">外观设计</option>
        </select>
      </div>
      <button class="btn btn-secondary btn-sm" @click="$emit('export-csv')" :disabled="!portfolio">📥 导出 CSV</button>
    </div>
    <div v-if="portfolio">
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div v-for="st in portfolio.stats" :key="st.ip_type" class="stat-card card">
          <span class="stat-icon">{{ ipTypeIcons[st.ip_type] }}</span>
          <span class="stat-num">{{ st.total }}</span>
          <span class="stat-label">{{ st.label }}</span>
          <div class="stat-detail">
            <span v-for="(count, status) in st.by_status" :key="status" class="mini-badge" :class="'badge-' + (statusVariants[status] || 'info')">
              {{ statusLabels[status] || status }}: {{ count }}
            </span>
          </div>
        </div>
      </div>

      <!-- 汇总 -->
      <div class="summary-row card">
        <div class="summary-item">
          <strong>{{ portfolio.total_ips }}</strong>
          <span>IP 总数</span>
        </div>
        <div class="summary-item">
          <strong>{{ portfolio.registered_count }}</strong>
          <span>已注册</span>
        </div>
        <div class="summary-item">
          <strong>{{ portfolio.pending_count }}</strong>
          <span>处理中</span>
        </div>
        <div class="summary-item">
          <strong>¥{{ portfolio.total_annual_cost.toLocaleString() }}</strong>
          <span>年度费用预估</span>
        </div>
      </div>

      <!-- 辖区分布 -->
      <div v-if="portfolio.by_jurisdiction && Object.keys(portfolio.by_jurisdiction).length" class="jurisdiction-stats card">
        <h4>🌍 地域分布</h4>
        <div class="jur-tags">
          <span v-for="(count, jur) in portfolio.by_jurisdiction" :key="jur" class="jur-tag">
            {{ jurisdictionFlags[jur] || '' }} {{ jurisdictionLabels[jur] || jur }} ×{{ count }}
          </span>
        </div>
      </div>

      <!-- 续展提醒 -->
      <div v-if="portfolio.renewals && portfolio.renewals.length" class="renewals-section card">
        <h4>⏰ 续展提醒</h4>
        <div class="renewal-list">
          <div v-for="r in portfolio.renewals" :key="r.id" class="renewal-item" :class="'urgency-' + r.urgency">
            <span class="urgency-dot">{{ r.urgency === 'red' ? '🔴' : r.urgency === 'orange' ? '🟡' : '🟢' }}</span>
            <div class="renewal-info">
              <strong>{{ r.ip_type_label || r.ip_type }} {{ r.jurisdiction_label ? '(' + r.jurisdiction_label + ')' : '' }}</strong>
              <span>{{ r.application_no || r.registration_no || '—' }}</span>
            </div>
            <div class="renewal-date">
              <span class="days-left" :class="'d-' + r.urgency">{{ r.days_remaining }}天</span>
              <small>{{ r.next_action_date }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
    <EmptyState v-else icon="📊" title="暂无IP资产" description="添加登记记录后将在此展示IP资产总览" />
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/common/EmptyState.vue'

defineProps<{
  activeTab: string
  portfolio: any
  dashFilterType: string
  typeLabels: Record<string, string>
  statusLabels: Record<string, string>
  statusVariants: Record<string, string>
  jurisdictionLabels: Record<string, string>
  jurisdictionFlags: Record<string, string>
  ipTypeIcons: Record<string, string>
}>()

defineEmits<{
  'update:dashFilterType': [type: string]
  'load-portfolio': []
  'export-csv': []
}>()
</script>

<style scoped>
/* ── Dashboard ───────────────────────────────── */
.dashboard { display:flex; flex-direction:column; gap:16px; }
.actions-bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.filter-group { display:flex; gap:8px; }
.filter-group .form-input { width:120px; padding:8px 12px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.stat-card { padding:20px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; }
.stat-icon { font-size:1.8rem; }
.stat-num { font-size:2rem; font-weight:800; color:var(--accent); }
.stat-label { font-size:.82rem; color:var(--muted); }
.stat-detail { display:flex; gap:4px; flex-wrap:wrap; justify-content:center; margin-top:4px; }
.mini-badge { font-size:.65rem; padding:1px 5px; border-radius:var(--m-radius-xs, 6px); }
.badge-info { background:rgba(124, 124, 129, 0.1); color:var(--blue); }
.badge-success { background:rgba(86,202,0,0.1); color:var(--accent); }
.badge-warning { background:rgba(129, 129, 133, 0.1); color:var(--orange); }
.badge-error { background:rgba(129, 129, 133, 0.1); color:var(--red); }

.summary-row { padding:20px; display:flex; gap:32px; }
.summary-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.summary-item strong { font-size:1.4rem; color:var(--accent); }
.summary-item span { font-size:.8rem; color:var(--muted); }

.jurisdiction-stats { padding:20px; }
.jurisdiction-stats h4 { margin:0 0 10px; font-size:.95rem; }
.jur-tags { display:flex; gap:8px; flex-wrap:wrap; }
.jur-tag { padding:6px 14px; background:var(--surface); border:1px solid var(--border); border-radius:100px; font-size:.82rem; font-weight:600; }

.renewals-section { padding:20px; }
.renewals-section h4 { margin:0 0 12px; font-size:.95rem; }
.renewal-list { display:flex; flex-direction:column; gap:8px; }
.renewal-item { display:flex; align-items:center; gap:12px; padding:12px; border-radius:var(--m-radius-sm); border:1px solid var(--border); }
.urgency-red { border-left:4px solid var(--red); background:rgba(129, 129, 133, 0.03); }
.urgency-orange { border-left:4px solid var(--orange); background:rgba(129, 129, 133, 0.03); }
.urgency-dot { font-size:1rem; }
.renewal-info { flex:1; display:flex; flex-direction:column; }
.renewal-info strong { font-size:.85rem; }
.renewal-info span { font-size:.76rem; color:var(--muted); }
.renewal-date { text-align:right; }
.days-left { font-weight:800; font-size:1rem; }
.d-red { color:var(--red); }
.d-orange { color:var(--orange); }
.renewal-date small { display:block; font-size:.72rem; color:var(--muted); }
</style>
