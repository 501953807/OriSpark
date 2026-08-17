<template>
  <div class="pod-profit-view">
    <div v-if="errorMsg" class="error-toast" @click="errorMsg = ''">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-toast">{{ successMsg }}</div>

    <!-- Overview stats -->
    <div class="stats-grid stats-grid-4">
      <div class="stat-card">
        <div class="stat-value">{{ overview?.total_sales ?? 0 }}</div>
        <div class="stat-label">总销量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #52c41a">¥{{ formatNum(overview?.total_revenue_cny ?? 0) }}</div>
        <div class="stat-label">总收入</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #fa8c16">¥{{ formatNum(overview?.total_cost_cny ?? 0) }}</div>
        <div class="stat-label">总成本</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #1890ff">¥{{ formatNum(overview?.total_profit_cny ?? 0) }}</div>
        <div class="stat-label">总利润</div>
      </div>
    </div>

    <!-- Pricing simulator -->
    <div class="card">
      <div class="card-header">
        <h3>定价模拟器</h3>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">平台</label>
          <select class="form-select" v-model="simForm.platform">
            <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">产品类型</label>
          <select class="form-select" v-model="simForm.product_type">
            <option value="tshirt">T恤</option>
            <option value="mug">马克杯</option>
            <option value="poster">海报</option>
            <option value="phone_case">手机壳</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">加价率</label>
          <input class="form-input" type="number" v-model.number="simForm.markup_rate" min="0.1" max="2" step="0.05" />
        </div>
        <button class="btn btn-primary" @click="handleSimulate" :disabled="loading">模拟</button>
      </div>
      <table class="data-table" v-if="simulations.length > 0">
        <thead>
          <tr>
            <th>加价率</th>
            <th>售价 (USD)</th>
            <th>售价 (CNY)</th>
            <th>利润 (USD)</th>
            <th>利润 (CNY)</th>
            <th>利润率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in simulations" :key="s.markup_pct">
            <td>{{ (s.markup_pct * 100).toFixed(0) }}%</td>
            <td>${{ s.sale_price_usd.toFixed(2) }}</td>
            <td>¥{{ s.sale_price_cny.toFixed(2) }}</td>
            <td style="color: #52c41a">${{ s.profit_usd.toFixed(2) }}</td>
            <td style="color: #52c41a">¥{{ s.profit_cny.toFixed(2) }}</td>
            <td>{{ (s.margin_pct * 100).toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Record sale -->
    <div class="card">
      <div class="card-header">
        <h3>记录销售</h3>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">平台</label>
          <select class="form-select" v-model="saleForm.platform">
            <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">产品类型</label>
          <select class="form-select" v-model="saleForm.product_type">
            <option value="tshirt">T恤</option>
            <option value="mug">马克杯</option>
            <option value="poster">海报</option>
            <option value="phone_case">手机壳</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">售价 (USD)</label>
          <input class="form-input" type="number" v-model.number="saleForm.sale_price_usd" min="0" step="0.01" />
        </div>
        <div class="form-group">
          <label class="form-label">成本 (USD)</label>
          <input class="form-input" type="number" v-model.number="saleForm.base_cost_usd" min="0" step="0.01" />
        </div>
        <button class="btn btn-accent" @click="handleRecordSale" :disabled="loading">记录</button>
      </div>
      <div v-if="lastProfit" class="profit-result">
        利润: <strong style="color: #52c41a">¥{{ lastProfit.profit_cny.toFixed(2) }}</strong>
        (利润率 {{ (lastProfit.margin_pct * 100).toFixed(1) }}%)
      </div>
    </div>

    <!-- Design summary -->
    <div class="card">
      <div class="card-header">
        <h3>设计利润汇总</h3>
        <button class="btn btn-sm btn-secondary" @click="loadDesigns" :disabled="loading">刷新</button>
      </div>
      <table class="data-table" v-if="designs.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>状态</th>
            <th>销量</th>
            <th>收入 (CNY)</th>
            <th>利润 (CNY)</th>
            <th>平均利润率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in designs" :key="d.id">
            <td>{{ d.id.slice(0, 8) }}...</td>
            <td>{{ d.title }}</td>
            <td><span class="badge" :class="d.status === 'active' ? 'badge-success' : 'badge-default'">{{ d.status }}</span></td>
            <td>{{ d.total_sales }}</td>
            <td>¥{{ formatNum(d.total_revenue_cny) }}</td>
            <td style="color: #52c41a">¥{{ formatNum(d.total_profit_cny) }}</td>
            <td>{{ (d.avg_margin_pct * 100).toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="!loading" class="empty-state">暂无设计数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePodProfitStore } from '@/stores/usePodProfitStore'

const store = usePodProfitStore()

const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const platforms = ['redbubble', 'printful', 'amazon']

const simForm = ref({
  platform: 'redbubble',
  product_type: 'tshirt',
  markup_rate: 0.3,
})

const saleForm = ref({
  platform: 'redbubble',
  product_type: 'tshirt',
  sale_price_usd: 25,
  base_cost_usd: 8,
})

const overview = ref(store.overview)
const designs = ref(store.designs)
const simulations = ref(store.simulations)
const lastProfit = ref(store.lastProfit)

async function loadOverview() {
  await store.loadOverview()
  overview.value = store.overview
}

async function loadDesigns() {
  await store.loadDesigns()
  designs.value = store.designs
}

async function handleSimulate() {
  loading.value = true
  try {
    await store.simulatePricing(simForm.value.platform, simForm.value.product_type, simForm.value.markup_rate)
    simulations.value = store.simulations
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '模拟失败'
  } finally {
    loading.value = false
  }
}

async function handleRecordSale() {
  loading.value = true
  try {
    await store.recordSale({
      platform: saleForm.value.platform,
      product_type: saleForm.value.product_type,
      sale_price_usd: saleForm.value.sale_price_usd,
      base_cost_usd: saleForm.value.base_cost_usd,
    })
    overview.value = store.overview
    lastProfit.value = store.lastProfit
    successMsg.value = '销售记录成功'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '记录失败'
  } finally {
    loading.value = false
  }
}

function formatNum(n: number): string {
  return n.toFixed(2)
}

onMounted(() => {
  loadOverview()
  loadDesigns()
})
</script>

<style scoped>
.pod-profit-view { display: flex; flex-direction: column; gap: 16px; }

.form-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.form-row .form-group { flex: 1; min-width: 120px; }

.profit-result {
  margin-top: 12px; padding: 12px; background: var(--m-bg-subtle);
  border-radius: var(--m-radius-sm); font-size: 0.9rem;
}

.error-toast {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 12px 20px; background: var(--red); color: #fff;
  border-radius: var(--m-radius-sm); font-size: 0.85rem; cursor: pointer;
  box-shadow: 0 4px 12px oklch(0 0 0 / .15); animation: slideIn .2s ease;
}
.success-toast {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 12px 20px; background: oklch(55% 0.12 150); color: #fff;
  border-radius: var(--m-radius-sm); font-size: 0.85rem;
  box-shadow: 0 4px 12px oklch(0 0 0 / .15); animation: slideIn .2s ease;
}
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

.empty-state { padding: 32px; text-align: center; color: var(--m-grey-500); }
</style>
