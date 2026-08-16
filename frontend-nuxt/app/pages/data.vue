<template>
  <div class="page-data">
    <h1 class="page-title">数据看板</h1>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'overview' }]" @click="activeTab = 'overview'">
        平台总览
      </button>
      <button :class="['tab-btn', { active: activeTab === 'ranking' }]" @click="activeTab = 'ranking'">
        创作者排行
      </button>
      <button :class="['tab-btn', { active: activeTab === 'trends' }]" @click="activeTab = 'trends'">
        品类趋势
      </button>
      <button :class="['tab-btn', { active: activeTab === 'report' }]" @click="activeTab = 'report'">
        行业报告
      </button>
    </div>

    <!-- 平台总览 -->
    <div v-if="activeTab === 'overview'">
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-value">{{ stats.total_creators }}</div>
          <div class="stat-label">注册创作者</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🎨</div>
          <div class="stat-value">{{ stats.total_works }}</div>
          <div class="stat-label">作品总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-value">{{ stats.total_contracts }}</div>
          <div class="stat-label">合约总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ stats.active_contracts }}</div>
          <div class="stat-label">活跃合约</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-value mono">{{ formatCurrency(stats.monthly_transaction_volume) }}</div>
          <div class="stat-label">月交易额</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-value">{{ stats.avg_split_rate }}%</div>
          <div class="stat-label">平均分润率</div>
        </div>
      </div>
    </div>

    <!-- 创作者排行 -->
    <div v-if="activeTab === 'ranking'">
      <div class="filter-bar">
        <select v-model="sortMode" class="filter-select">
          <option value="works">按作品数</option>
          <option value="transactions">按成交额</option>
          <option value="scr">按SCR信誉</option>
        </select>
      </div>

      <div v-if="loadingRanking" class="loading-state">加载中...</div>
      <div v-else-if="rankingError" class="error-state">{{ rankingError }}</div>
      <div v-else class="ranking-table">
        <div class="table-header">
          <span class="col-rank">#</span>
          <span class="col-user">创作者</span>
          <span class="col-type">类型</span>
          <span v-if="sortMode === 'works'" class="col-stat">作品数</span>
          <span v-if="sortMode === 'transactions'" class="col-stat">成交额</span>
          <span v-if="sortMode === 'scr'" class="col-stat">SCR</span>
        </div>
        <div
          v-for="(item, idx) in rankingData"
          :key="item.user_id"
          :class="['table-row', idx < 3 ? 'top-ranker' : '']"
        >
          <span class="col-rank">{{ idx + 1 }}</span>
          <span class="col-user">
            <span class="username">{{ item.username }}</span>
            <span class="email">{{ item.email }}</span>
          </span>
          <span class="col-type">{{ CREATOR_TYPE_LABEL[item.creator_type || ''] || item.creator_type || '-' }}</span>
          <span v-if="sortMode === 'works'" class="col-stat mono">{{ item.work_count }}</span>
          <span v-if="sortMode === 'transactions'" class="col-stat mono">{{ formatCurrency(item.total_transactions) }}</span>
          <span v-if="sortMode === 'scr'" class="col-stat">
            <span class="mono">{{ typeof item.scr_score === 'number' ? item.scr_score.toFixed(1) : '-' }}</span>
            <span
              v-if="item.rating_level && RATING_LEVEL_LABEL[item.rating_level]"
              class="rating-badge"
              :style="{ color: RATING_LEVEL_COLOR[item.rating_level] }"
            >
              {{ RATING_LEVEL_LABEL[item.rating_level] }}
            </span>
          </span>
        </div>
      </div>
      <div v-if="!rankingData.length && !loadingRanking" class="empty-state">暂无创作者数据</div>
    </div>

    <!-- 品类趋势 -->
    <div v-if="activeTab === 'trends'">
      <div class="filter-bar">
        <select v-model="periodMode" class="filter-select">
          <option value="monthly">月度</option>
          <option value="quarterly">季度</option>
        </select>
      </div>

      <div v-if="loadingTrends" class="loading-state">加载中...</div>
      <div v-else-if="trendsError" class="error-state">{{ trendsError }}</div>
      <div v-else class="trends-grid">
        <div
          v-for="trend in trendsData"
          :key="trend.category"
          class="trend-card"
        >
          <div class="trend-header">
            <span class="trend-category">{{ CREATOR_TYPE_LABEL[trend.category] || trend.category }}</span>
            <span class="trend-count">{{ trend.work_count }}</span>
          </div>
          <div class="trend-bar">
            <div
              class="trend-bar-fill"
              :style="{ width: `${(trend.work_count / maxTrendCount) * 100}%` }"
            ></div>
          </div>
          <span class="trend-period">{{ trend.period }}</span>
        </div>
      </div>
      <div v-if="!trendsData.length && !loadingTrends" class="empty-state">暂无品类数据</div>
    </div>

    <!-- 行业报告 -->
    <div v-if="activeTab === 'report'">
      <div class="filter-bar">
        <input
          v-model="reportMonth"
          type="month"
          class="input-date"
          @change="loadReport"
        />
        <button class="btn-primary" @click="loadReport">生成报告</button>
      </div>

      <div v-if="loadingReport" class="loading-state">加载中...</div>
      <div v-else-if="reportError" class="error-state">{{ reportError }}</div>
      <div v-else class="report-card">
        <div class="report-header">
          <h2 class="report-title">{{ report.report_month }} 创作者经济报告</h2>
          <span class="report-time">{{ formatDateTime(report.generated_at) }}</span>
        </div>
        <div class="report-summary">{{ report.summary }}</div>
        <div class="report-stats">
          <div class="report-stat">
            <span class="stat-num">{{ report.total_creators }}</span>
            <span class="stat-desc">新增创作者</span>
          </div>
          <div class="report-stat">
            <span class="stat-num">{{ report.total_works }}</span>
            <span class="stat-desc">新增作品</span>
          </div>
          <div class="report-stat">
            <span class="stat-num">{{ report.total_contracts }}</span>
            <span class="stat-desc">新增合约</span>
          </div>
          <div class="report-stat">
            <span class="stat-num mono">{{ formatCurrency(report.transaction_volume) }}</span>
            <span class="stat-desc">交易额</span>
          </div>
        </div>
        <div v-if="report.top_categories?.length" class="report-categories">
          <span class="categories-label">热门品类：</span>
          <span
            v-for="cat in report.top_categories"
            :key="cat"
            class="category-tag"
          >
            {{ CREATOR_TYPE_LABEL[cat] || cat }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'materio-topnav' })
import { ref, onMounted, computed, watch } from 'vue'
import {
  fetchPlatformStats,
  fetchCreatorRanking,
  fetchCategoryTrends,
  fetchIndustryReport,
} from '~/composables/useDataApi'
import {
  CREATOR_TYPE_LABEL, RATING_LEVEL_LABEL, RATING_LEVEL_COLOR,
  formatCurrency, formatDateTime,
} from '~/utils/data'

const auth = useAuthStore()
useHead({ title: '数据看板 — OriSpark' })

const activeTab = ref('overview')
const loading = ref(false)
const error = ref<string | null>(null)
const stats = ref<any>({})

// Ranking
const sortMode = ref('works')
const loadingRanking = ref(false)
const rankingError = ref<string | null>(null)
const rankingData = ref<any[]>([])

// Trends
const periodMode = ref('monthly')
const loadingTrends = ref(false)
const trendsError = ref<string | null>(null)
const trendsData = ref<any[]>([])
const maxTrendCount = computed(() => Math.max(...trendsData.value.map(t => t.work_count), 1))

// Report
const reportMonth = ref(new Date().toISOString().slice(0, 7))
const loadingReport = ref(false)
const reportError = ref<string | null>(null)
const report = ref<any>({})

async function loadStats() {
  loading.value = true
  error.value = null
  try {
    stats.value = await fetchPlatformStats()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadRanking() {
  loadingRanking.value = true
  rankingError.value = null
  try {
    rankingData.value = await fetchCreatorRanking({ sort_by: sortMode.value, limit: 20 })
  } catch (e) {
    rankingError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingRanking.value = false
  }
}

async function loadTrends() {
  loadingTrends.value = true
  trendsError.value = null
  try {
    trendsData.value = await fetchCategoryTrends({ period: periodMode.value, limit: 10 })
  } catch (e) {
    trendsError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingTrends.value = false
  }
}

async function loadReport() {
  loadingReport.value = true
  reportError.value = null
  try {
    report.value = await fetchIndustryReport(reportMonth.value)
  } catch (e) {
    reportError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingReport.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'overview') loadStats()
  else if (tab === 'ranking') loadRanking()
  else if (tab === 'trends') loadTrends()
  else if (tab === 'report') loadReport()
})

watch(sortMode, loadRanking)
watch(periodMode, loadTrends)

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.page-data {
  padding: 32px;
  max-width: 1100px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--spark-text);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--spark-border);
  padding-bottom: 0;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--spark-muted);
  transition: all 0.2s;
}

.tab-btn.active {
  color: var(--spark-gold);
  border-bottom-color: var(--spark-gold);
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
}

.filter-select, .input-date {
  padding: 10px 16px;
  border: 1px solid var(--spark-border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--spark-surface);
  color: var(--spark-text);
}

.btn-primary {
  padding: 10px 20px;
  background: var(--spark-gold);
  color: #0f172a;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-primary:hover {
  background: #c4a030;
}

/* 平台总览 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--spark-surface);
  border: 1px solid var(--spark-border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.stat-card:hover {
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.12);
  border-color: rgba(212, 175, 55, 0.3);
}

.stat-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--spark-gold);
  margin-bottom: 4px;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
}

.stat-label {
  font-size: 13px;
  color: var(--spark-muted);
}

/* 创作者排行 */
.ranking-table {
  background: var(--spark-surface);
  border: 1px solid var(--spark-border);
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 50px 1fr 100px 100px;
  padding: 12px 16px;
  background: var(--spark-bg);
  border-bottom: 1px solid var(--spark-border);
  font-size: 13px;
  font-weight: 600;
  color: var(--spark-muted);
}

.table-row {
  display: grid;
  grid-template-columns: 50px 1fr 100px 100px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--spark-border);
  align-items: center;
  transition: background 0.15s;
}

.table-row:hover {
  background: rgba(212, 175, 55, 0.05);
}

.table-row.top-ranker {
  background: rgba(212, 175, 55, 0.08);
}

.table-row:last-child {
  border-bottom: none;
}

.col-rank {
  font-size: 14px;
  font-weight: 600;
  color: var(--spark-gold);
}

.col-user {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: var(--spark-text);
}

.email {
  font-size: 12px;
  color: var(--spark-muted);
}

.col-type {
  font-size: 13px;
  color: var(--spark-muted);
}

.col-stat {
  font-size: 14px;
  color: var(--spark-text);
}

.rating-badge {
  font-size: 12px;
  font-weight: 600;
  margin-left: 4px;
}

/* 品类趋势 */
.trends-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-card {
  background: var(--spark-surface);
  border: 1px solid var(--spark-border);
  border-radius: 12px;
  padding: 16px 20px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.trend-category {
  font-size: 15px;
  font-weight: 600;
  color: var(--spark-text);
}

.trend-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--spark-gold);
}

.trend-bar {
  height: 8px;
  background: var(--spark-bg);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}

.trend-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--spark-gold), var(--spark-silver));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.trend-period {
  font-size: 12px;
  color: var(--spark-muted);
}

/* 行业报告 */
.report-card {
  background: var(--spark-surface);
  border: 1px solid var(--spark-border);
  border-radius: 12px;
  padding: 24px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--spark-border);
}

.report-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: var(--spark-text);
}

.report-time {
  font-size: 13px;
  color: var(--spark-muted);
}

.report-summary {
  font-size: 15px;
  line-height: 1.7;
  color: var(--spark-text);
  margin-bottom: 24px;
  padding: 16px;
  background: var(--spark-bg);
  border-radius: 8px;
}

.report-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.report-stat {
  text-align: center;
  padding: 16px;
  background: var(--spark-bg);
  border-radius: 8px;
}

.stat-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--spark-gold);
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 13px;
  color: var(--spark-muted);
}

.report-categories {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.categories-label {
  font-size: 14px;
  color: var(--spark-text);
  font-weight: 500;
}

.category-tag {
  padding: 4px 12px;
  background: rgba(212, 175, 55, 0.12);
  color: var(--spark-gold);
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--spark-muted);
}

.error-state {
  color: var(--spark-red);
}
</style>
