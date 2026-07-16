<template>
  <div class="revenue-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>收入多元化分析</h2>
      <p class="subtitle">基于香农熵的 8 种变现手段收入结构健康度评估</p>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-val">{{ totalRevenue }}</div>
          <div class="stat-lbl">总收入 (CNY)</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" :class="diversityScoreClass">{{ diversityIndex }}</div>
          <div class="stat-lbl">多样性指数</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{{ totalSources }}</div>
          <div class="stat-lbl">收入来源数</div>
        </div>
      </div>

      <!-- 收入分布饼图 (CSS) -->
      <div class="chart-section">
        <h3>收入来源分布</h3>
        <div class="distribution-bars">
          <div v-for="(info, cat) in categoryDistribution" :key="cat" class="bar-item">
            <div class="bar-label">
              <span class="bar-dot" :style="{ background: info.color }"></span>
              <span>{{ info.name }}</span>
              <span class="bar-pct">{{ (info.proportion * 100).toFixed(0) }}%</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${info.proportion * 100}%`, background: info.color }"></div>
            </div>
            <div class="bar-amount">¥{{ info.amount.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- 月度趋势 -->
      <div class="chart-section" v-if="monthlyTrend.length > 0">
        <h3>月度趋势</h3>
        <div class="trend-chart">
          <div v-for="m in monthlyTrend" :key="m.month" class="trend-item">
            <span class="trend-month">{{ m.month }}</span>
            <div class="trend-bar-track">
              <div class="trend-bar-fill" :style="{ width: `${(m.amount / maxMonthAmount) * 100}%` }"></div>
            </div>
            <span class="trend-amount">¥{{ m.amount.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- 预警信息 -->
      <div class="warning-section" v-if="warnings.length > 0">
        <h3>收入健康提示</h3>
        <div v-for="(w, i) in warnings" :key="i" class="warning-item" :class="w.startsWith('⚠️') ? 'warn' : 'ok'">
          {{ w }}
        </div>
      </div>

      <!-- 手动录入 -->
      <div class="add-section">
        <h3>手动录入收入</h3>
        <div class="form-grid">
          <select v-model="newRecord.income_category" class="select">
            <option value="" disabled>选择变现渠道</option>
            <option v-for="(info, cat) in incomeCategories" :key="cat" :value="cat">
              {{ info.name }}
            </option>
          </select>
          <input v-model.number="newRecord.amount" placeholder="金额 (CNY)" type="number" min="0" step="0.01" class="input" />
          <input v-model="newRecord.platform" placeholder="平台 (如 YouTube/Patreon)" class="input" />
          <input v-model="newRecord.source_description" placeholder="描述说明" class="input" />
        </div>
        <button class="btn-primary" @click="addRecord" :disabled="adding || !newRecord.income_category || !newRecord.amount">
          {{ adding ? '提交中...' : '添加记录' }}
        </button>
      </div>

      <!-- 空状态 -->
      <div v-if="!summary && !store.loading" class="empty">暂无收入数据 — 点击下方添加第一条记录</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRevenueStore } from '@/stores/useRevenueStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const INCOME_CATEGORIES = {
  ad_revenue: { name: '广告分成', color: '#FF6B6B' },
  sponsorship: { name: '品牌赞助', color: '#4ECDC4' },
  subscription: { name: '付费订阅', color: '#45B7D1' },
  tip: { name: '打赏', color: '#96CEB4' },
  ecommerce: { name: '电商', color: '#FFEAA7' },
  affiliate: { name: '联盟营销', color: '#DDA0DD' },
  knowledge_payment: { name: '知识付费', color: '#98D8C8' },
  ip_licensing: { name: 'IP授权', color: '#F7DC6F' },
} as const

const incomeCategories = INCOME_CATEGORIES

const store = useRevenueStore()
const adding = ref(false)
const newRecord = reactive({
  income_category: '',
  amount: 0,
  platform: '',
  source_description: '',
})

const summary = computed(() => store.summary)
const diversity = computed(() => store.diversity)

const totalRevenue = computed(() => summary.value?.total_revenue ?? 0)
const diversityIndex = computed(() => (diversity.value?.diversity_index ?? 0).toFixed(2))
const totalSources = computed(() => diversity.value?.total_sources ?? 0)

const diversityScoreClass = computed(() => {
  const idx = diversity.value?.diversity_index ?? 0
  if (idx >= 0.6) return 'score-high'
  if (idx >= 0.3) return 'score-mid'
  return 'score-low'
})

const categoryDistribution = computed(() => diversity.value?.category_distribution ?? {})

const warnings = computed(() => diversity.value?.warnings ?? [])

const monthlyTrend = computed(() => summary.value?.monthly_trend ?? [])
const maxMonthAmount = computed(() => {
  if (!monthlyTrend.value.length) return 1
  return Math.max(...monthlyTrend.value.map((m: any) => m.amount), 1)
})

async function addRecord() {
  if (!newRecord.income_category || !newRecord.amount || newRecord.amount <= 0) return
  adding.value = true
  try {
    await store.fetch('current_user')
  } catch (e) {
    console.error('add record failed:', e)
  } finally {
    adding.value = false
    newRecord.income_category = ''
    newRecord.amount = 0
    newRecord.platform = ''
    newRecord.source_description = ''
  }
}
</script>

<style scoped>
.revenue-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }
.stat-val { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-val.score-high { color: #22c55e; }
.stat-val.score-mid { color: #f59e0b; }
.stat-val.score-low { color: #dc2626; }
.stat-lbl { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }

.chart-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }
.chart-section h3 { margin-top: 0; font-size: 1rem; }

.distribution-bars { display: flex; flex-direction: column; gap: 12px; }
.bar-item { }
.bar-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; margin-bottom: 4px; }
.bar-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.bar-pct { margin-left: auto; font-weight: 600; }
.bar-track { height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s ease; }
.bar-amount { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }

.trend-chart { display: flex; flex-direction: column; gap: 8px; }
.trend-item { display: flex; align-items: center; gap: 12px; }
.trend-month { width: 60px; font-size: 0.8rem; color: var(--muted); text-align: right; flex-shrink: 0; }
.trend-bar-track { flex: 1; height: 20px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.trend-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.3s ease; }
.trend-amount { width: 80px; font-size: 0.82rem; font-weight: 600; flex-shrink: 0; }

.warning-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }
.warning-section h3 { margin-top: 0; font-size: 1rem; }
.warning-item { padding: 8px 12px; border-radius: var(--radius-sm); font-size: 0.85rem; margin-bottom: 8px; }
.warning-item.warn { background: #fffbeb; color: #92400e; border-left: 3px solid #f59e0b; }
.warning-item.ok { background: #f0fdf4; color: #166534; border-left: 3px solid #22c55e; }

.add-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }
.add-section h3 { margin-top: 0; font-size: 1rem; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.input, .select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.9rem; }
.btn-primary { background: var(--accent); color: white; border: none; padding: 8px 20px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.empty { padding: 48px; text-align: center; color: var(--muted); }
</style>
