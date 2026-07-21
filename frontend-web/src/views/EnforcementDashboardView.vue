<template>
  <div class="enforcement-dashboard">
    <!-- Header -->
    <div class="header">
      <h2>维权流水线</h2>
      <p class="subtitle">追踪从侵权发现到投诉解决的完整生命周期</p>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <StatCard icon="📋" label="总行动" :value="stats.total" color="blue" />
      <StatCard icon="⏳" label="待审核" :value="stats.pending" color="orange" />
      <StatCard icon="📍" label="取证中" :value="stats.evidence" color="purple" />
      <StatCard icon="📤" label="已提交" :value="stats.filed" color="green" />
      <StatCard icon="✅" label="已解决" :value="stats.resolved" color="teal" />
    </div>

    <!-- Filters -->
    <div class="filters card">
      <div class="filter-row">
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option value="pending_review">待审核</option>
          <option value="confirmed">已确认</option>
          <option value="evidence_gathered">取证中</option>
          <option value="complaint_filed">已提交</option>
          <option value="resolved">已解决</option>
        </select>
        <select v-model="filterPlatform" class="filter-select">
          <option value="">全部平台</option>
          <option value="generic">通用</option>
          <option value="xiaohongshu">小红书</option>
          <option value="instagram">Instagram</option>
          <option value="taobao">淘宝</option>
          <option value="youtube">YouTube</option>
        </select>
        <button class="btn btn-secondary btn-sm" @click="refresh">刷新</button>
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-if="!loading && filteredActions.length === 0"
      icon="⚖️"
      title="暂无维权记录"
      description="从作品详情页点击'维权'按钮开始维权流程，或等待侵权监测发现侵权行为。"
    >
      <router-link to="/app/works" class="btn btn-primary" style="margin-top:16px">
        前往作品列表
      </router-link>
    </EmptyState>

    <!-- Action list -->
    <div v-else class="actions-grid">
      <div v-for="action in filteredActions" :key="action.id" class="action-card card">
        <div class="action-header">
          <StatusBadge
            :status="action.status"
            :labels="statusLabels"
            :variants="statusVariants"
          />
          <span class="action-platform">{{ platformLabel(action.platform) }}</span>
        </div>

        <div class="action-meta">
          <div class="meta-item">
            <span class="label">类型</span>
            <span class="value">{{ actionTypeLabel(action.action_type) }}</span>
          </div>
          <div class="meta-item" v-if="action.work_title">
            <span class="label">作品</span>
            <span class="value">{{ action.work_title }}</span>
          </div>
          <div class="meta-item" v-if="action.similarity_score != null">
            <span class="label">相似度</span>
            <span class="value" :class="similarityClass(action.similarity_score)">
              {{ (action.similarity_score * 100).toFixed(0) }}%
            </span>
          </div>
        </div>

        <div class="action-infringement" v-if="action.infringement_url">
          <span class="label">侵权链接</span>
          <a :href="action.infringement_url" target="_blank" rel="noopener" class="mono">
            {{ truncateUrl(action.infringement_url) }}
          </a>
        </div>

        <div class="action-footer">
          <span class="action-date">创建于 {{ formatDate(action.created_at) }}</span>
          <router-link
            v-if="action.work_id"
            :to="`/app/works/${action.work_id}`"
            class="view-link"
          >
            查看作品 &rarr;
          </router-link>
        </div>
      </div>
    </div>

    <!-- Templates section -->
    <div class="templates-section card">
      <div class="templates-header">
        <h3>投诉模板</h3>
        <button class="btn btn-secondary btn-sm" @click="handleSeed">初始化默认模板</button>
      </div>
      <div v-if="templateLoading" class="loading-hint">加载中...</div>
      <div v-else-if="templates.length" class="template-list">
        <div v-for="tpl in templates" :key="tpl.id" class="template-item">
          <strong>{{ tpl.title }}</strong>
          <span class="tpl-badge">{{ tpl.platform }}</span>
          <span class="tpl-badge">{{ tpl.jurisdiction }}</span>
        </div>
      </div>
      <div v-else class="empty-hint">
        <p>暂无可用模板，点击上方按钮初始化。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { EnforcementAction, EnforcementTemplate } from '@/types/enforcement'
import { enforcementApi } from '@/api/enforcement'

// ------------------------------------------------------------------
// State
// ------------------------------------------------------------------

const loading = ref(false)
const actions = ref<EnforcementAction[]>([])
const templates = ref<EnforcementTemplate[]>([])
const templateLoading = ref(false)
const filterStatus = ref('')
const filterPlatform = ref('')

// ------------------------------------------------------------------
// Stats
// ------------------------------------------------------------------

const stats = computed(() => ({
  total: actions.value.length,
  pending: actions.value.filter(a => a.status === 'pending_review').length,
  evidence: actions.value.filter(a => a.status === 'evidence_gathered').length,
  filed: actions.value.filter(a => a.status === 'complaint_filed').length,
  resolved: actions.value.filter(a => a.status === 'resolved').length,
}))

// ------------------------------------------------------------------
// Filtering
// ------------------------------------------------------------------

const filteredActions = computed(() => {
  let result = actions.value
  if (filterStatus.value) {
    result = result.filter(a => a.status === filterStatus.value)
  }
  if (filterPlatform.value) {
    result = result.filter(a => a.platform === filterPlatform.value)
  }
  return result
})

// ------------------------------------------------------------------
// Display helpers
// ------------------------------------------------------------------

const statusLabels: Record<string, string> = {
  pending_review: '待审核',
  confirmed: '已确认',
  evidence_gathered: '取证中',
  complaint_filed: '已提交',
  resolved: '已解决',
}

const statusVariants: Record<string, string> = {
  pending_review: 'warning',
  confirmed: 'info',
  evidence_gathered: 'info',
  complaint_filed: 'success',
  resolved: 'confirmed',
}

function actionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    platform_complaint: '平台投诉',
    dmca_notice: 'DMCA通知',
    lawyer_letter: '律师函',
    litigation: '诉讼',
  }
  return map[type] || type
}

function platformLabel(platform: string): string {
  const map: Record<string, string> = {
    generic: '通用',
    xiaohongshu: '小红书',
    instagram: 'Instagram',
    taobao: '淘宝',
    youtube: 'YouTube',
    weibo: '微博',
    douyin: '抖音',
  }
  return map[platform] || platform
}

function similarityClass(score: number): string {
  if (score >= 0.8) return 'high'
  if (score >= 0.5) return 'mid'
  return 'low'
}

function truncateUrl(url: string): string {
  if (url.length <= 60) return url
  return url.slice(0, 57) + '...'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return dateStr.slice(0, 16).replace('T', ' ')
}

// ------------------------------------------------------------------
// API calls
// ------------------------------------------------------------------

async function refresh() {
  loading.value = true
  try {
    const res = await enforcementApi.listTemplates()
    templates.value = res.data || []
  } catch {
    templates.value = []
  } finally {
    loading.value = false
  }
}

async function handleSeed() {
  try {
    await enforcementApi.seedTemplates()
    await refresh()
    ;(window as any).$toast?.show('模板已初始化', 'success')
  } catch {
    ;(window as any).$toast?.show('模板初始化失败', 'error')
  }
}

onMounted(refresh)
</script>

<style scoped>
.enforcement-dashboard { display: flex; flex-direction: column; gap: 24px; }

/* Header */
.header h2 { font-size: 1.4rem; margin: 0 0 4px; }
.subtitle { font-size: 0.85rem; color: var(--muted); margin: 0; }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 600px) { .stats-row { grid-template-columns: 1fr; } }

/* Filters */
.filters { padding: 16px; }
.filter-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.filter-select {
  padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface); color: var(--fg); font-size: 0.85rem;
  font-family: var(--font-body); cursor: pointer;
}

/* Actions grid */
.actions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }

.action-card { padding: 16px; display: flex; flex-direction: column; gap: 10px; }

.action-header { display: flex; align-items: center; justify-content: space-between; }
.action-platform {
  font-size: 0.72rem; padding: 2px 8px; border-radius: 100px;
  background: var(--border); color: var(--muted); text-transform: uppercase; font-weight: 600;
}

.action-meta { display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.82rem; }
.meta-item { display: flex; gap: 6px; }
.meta-item .label { color: var(--muted); font-weight: 600; font-size: 0.75rem; }
.meta-item .value { color: var(--fg); }
.similarity-class.high { color: #e53e3e; font-weight: 700; }
.similarity-class.mid { color: var(--orange); font-weight: 600; }

.action-infringement {
  display: flex; gap: 6px; font-size: 0.78rem; align-items: baseline;
}
.action-infringement .label { color: var(--muted); font-weight: 600; font-size: 0.72rem; }
.action-infringement a {
  color: var(--accent); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  flex: 1; font-size: 0.75rem;
}

.action-footer {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 0.72rem; color: var(--muted);
}
.view-link { color: var(--accent); font-weight: 600; }

/* Templates */
.templates-section { padding: 16px; }
.templates-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;
}
.templates-header h3 { margin: 0; font-size: 0.95rem; font-weight: 700; }
.template-list { display: flex; flex-wrap: wrap; gap: 8px; }
.template-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.82rem;
}
.tpl-badge {
  font-size: 0.7rem; padding: 1px 6px; border-radius: 100px;
  background: var(--border); color: var(--muted);
}
.loading-hint { font-size: 0.82rem; color: var(--muted); text-align: center; padding: 16px; }
.empty-hint { text-align: center; color: var(--muted); font-size: 0.82rem; padding: 12px; }
</style>
