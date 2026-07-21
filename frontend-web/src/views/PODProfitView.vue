<template>
  <div class="pod-profit-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>POD 利润计算器</h2>
      <p class="subtitle">Print-on-Demand 定价模拟 · 利润追踪</p>

      <!-- 概览 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ overview?.total_sales || 0 }}</div>
          <div class="stat-label">总销量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">¥{{ formatNum(overview?.total_revenue_cny) }}</div>
          <div class="stat-label">总收入</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">¥{{ formatNum(overview?.total_profit_cny) }}</div>
          <div class="stat-label">总利润</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ overview?.overall_margin_pct || 0 }}%</div>
          <div class="stat-label">利润率</div>
        </div>
      </div>

      <!-- 定价模拟 -->
      <div class="section">
        <h3>定价模拟</h3>
        <div class="simulate-form">
          <select v-model="simForm.platform" class="form-select">
            <option value="">选择平台</option>
            <option value="redbubble">Redbubble</option>
            <option value="printful">Printful</option>
            <option value="printify">Printify</option>
          </select>
          <select v-model="simForm.product_type" class="form-select">
            <option value="">产品类型</option>
            <option value="t-shirt">T恤</option>
            <option value="phone_case">手机壳</option>
            <option value="poster">海报</option>
            <option value="mug">马克杯</option>
            <option value="sticker">贴纸</option>
            <option value="tapestry">挂毯</option>
          </select>
          <input type="number" v-model.number="simForm.markup" min="0.1" max="1" step="0.05" placeholder="加价率 (0.2 = 20%)" class="form-input" />
          <button class="btn-confirm" @click="handleSimulate">模拟</button>
        </div>
        <div v-if="store.simulations.length > 0" class="simulation-table">
          <table>
            <thead>
              <tr>
                <th>加价率</th><th>售价 (USD)</th><th>售价 (CNY)</th>
                <th>利润 (USD)</th><th>利润 (CNY)</th><th>利润率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in store.simulations" :key="s.markup_pct" :class="{ best: s.margin_pct === maxMargin }">
                <td>{{ s.markup_pct }}%</td>
                <td>${{ s.sale_price_usd.toFixed(2) }}</td>
                <td>¥{{ s.sale_price_cny.toFixed(2) }}</td>
                <td>${{ s.profit_usd.toFixed(2) }}</td>
                <td>¥{{ s.profit_cny.toFixed(2) }}</td>
                <td>{{ s.margin_pct }}%</td>
              </tr>
            </tbody>
          </table>
          <p class="hint">最高利润率行已高亮</p>
        </div>
      </div>

      <!-- 记录销售 -->
      <div class="section">
        <h3>记录销售</h3>
        <div class="sale-form">
          <select v-model="saleForm.platform" class="form-select">
            <option value="">平台</option>
            <option value="redbubble">Redbubble</option>
            <option value="printful">Printful</option>
            <option value="printify">Printify</option>
          </select>
          <select v-model="saleForm.product_type" class="form-select">
            <option value="">产品类型</option>
            <option value="t-shirt">T恤</option>
            <option value="phone_case">手机壳</option>
            <option value="poster">海报</option>
            <option value="mug">马克杯</option>
            <option value="sticker">贴纸</option>
          </select>
          <input type="number" v-model.number="saleForm.sale_price_usd" placeholder="售价 USD" step="0.01" class="form-input" />
          <input type="number" v-model.number="saleForm.base_cost_usd" placeholder="基础成本 USD" step="0.01" class="form-input" />
          <button class="btn-confirm" @click="handleRecordSale">记录</button>
        </div>
        <div v-if="store.lastProfit" class="profit-result">
          <strong>本次利润:</strong> ¥{{ store.lastProfit.profit_cny.toFixed(2) }} ({{ store.lastProfit.margin_pct }}%)
        </div>
      </div>

      <!-- 设计作品汇总 -->
      <div class="section">
        <h3>设计作品利润汇总</h3>
        <div class="design-list">
          <div v-for="d in store.designs" :key="d.id" class="design-item">
            <div class="design-info">
              <strong>{{ d.title }}</strong>
              <span class="design-status">{{ statusLabel(d.status) }}</span>
            </div>
            <div class="design-stats">
              <span>{{ d.total_sales }} 笔销售</span>
              <span>¥{{ formatNum(d.total_profit_cny) }} 利润</span>
              <span :class="['margin', { good: d.avg_margin_pct > 20, bad: d.avg_margin_pct < 10 }]">
                {{ d.avg_margin_pct }}%
              </span>
            </div>
          </div>
          <div v-if="store.designs.length === 0" class="empty-state">暂无设计作品。</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { usePodProfitStore } from '@/stores/usePodProfitStore'

const store = usePodProfitStore()

// Expose store refs for template
const overview = store.overview

const simForm = ref({ platform: '', product_type: '', markup: 0.2 })
const saleForm = ref({ platform: '', product_type: '', sale_price_usd: 0, base_cost_usd: 0 })

const maxMargin = computed(() => {
  if (!store.simulations.length) return 0
  return Math.max(...store.simulations.map(s => s.margin_pct))
})

async function handleSimulate() {
  if (!simForm.value.platform || !simForm.value.product_type) return
  await store.simulatePricing(simForm.value.platform, simForm.value.product_type, simForm.value.markup)
}

async function handleRecordSale() {
  if (!saleForm.value.platform || !saleForm.value.product_type) return
  await store.recordSale({
    platform: saleForm.value.platform,
    product_type: saleForm.value.product_type,
    sale_price_usd: saleForm.value.sale_price_usd,
    base_cost_usd: saleForm.value.base_cost_usd,
  })
}

function formatNum(n?: number): string {
  if (n === undefined || n === null) return '0'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusLabel(s: string): string {
  return { draft: '草稿', published: '已发布', paused: '暂停' }[s] || s
}

onMounted(() => { store.loadOverview(); store.loadDesigns() })
</script>

<style scoped>
.pod-profit-view { max-width: 900px; margin: 0 auto; }
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }
.stat-value { font-size: 1.4rem; font-weight: 800; color: var(--accent); }
.stat-label { font-size: 0.8rem; color: var(--muted); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 1rem; }

.simulate-form, .sale-form { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.form-select, .form-input { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; flex: 1; min-width: 120px; }
.btn-confirm { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem; }

.simulation-table table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.simulation-table th { text-align: left; padding: 8px; border-bottom: 2px solid var(--border); color: var(--muted); }
.simulation-table td { padding: 8px; border-bottom: 1px solid var(--border); }
.simulation-table tr.best { background: #f0fdf4; font-weight: 700; }
.hint { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }

.profit-result { background: #f0fdf4; padding: 12px; border-radius: var(--radius-sm); font-size: 0.9rem; margin-top: 8px; }

.design-list { display: grid; gap: 8px; }
.design-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.design-info { display: flex; gap: 8px; align-items: center; }
.design-status { font-size: 0.75rem; color: var(--muted); }
.design-stats { display: flex; gap: 12px; font-size: 0.8rem; }
.margin { font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.margin.good { background: #dcfce7; color: #16a34a; }
.margin.bad { background: #fef2f2; color: #dc2626; }

.empty-state { text-align: center; color: var(--muted); padding: 16px; font-size: 0.85rem; }
</style>
