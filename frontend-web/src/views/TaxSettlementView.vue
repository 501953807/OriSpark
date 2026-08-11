<template>
  <div class="tax-settlement-view">
      <!-- 顶部统计 -->
      <div class="stats-grid stats-grid-4" style="margin-bottom: 16px">
        <div class="stat-card">
          <div class="stat-value" style="color: #52c41a">$ {{ stats.totalIncome }}</div>
          <div class="stat-label">总收入</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: #fa8c16">$ {{ stats.totalWithheld }}</div>
          <div class="stat-label">已预扣税</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: #ff4d4f">$ {{ stats.totalOwed }}</div>
          <div class="stat-label">应纳税</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.pendingReports }}</div>
          <div class="stat-label">待处理报告</div>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="tabs">
        <div class="tab-row">
          <button class="tab" :class="{ active: activeTab === 'calc' }" @click="activeTab = 'calc'">税务计算</button>
          <button class="tab" :class="{ active: activeTab === 'convert' }" @click="activeTab = 'convert'">货币转换</button>
          <button class="tab" :class="{ active: activeTab === 'agents' }" @click="activeTab = 'agents'">税务代理</button>
          <button class="tab" :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'">税务报告</button>
        </div>

        <!-- 税务计算 -->
        <div class="tab-panel" v-if="activeTab === 'calc'">
          <div class="card">
            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center">
              <span>实时税务计算</span>
              <button class="btn btn-primary" @click="showCalcModal = true">新计算</button>
            </div>

            <table class="data-table">
              <thead>
                <tr>
                  <th>产品类型</th>
                  <th>金额</th>
                  <th>税率</th>
                  <th>税额</th>
                  <th>司法管辖区</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in calcHistory" :key="row.id">
                  <td>{{ row.product_type }}</td>
                  <td>${{ row.amount.toFixed(2) }}</td>
                  <td>{{ ((row.tax_rate || 0) * 100).toFixed(1) }}%</td>
                  <td>${{ (row.tax_amount || 0).toFixed(2) }}</td>
                  <td>{{ row.tax_jurisdiction || '-' }}</td>
                  <td>{{ formatDate(row.calculated_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 货币转换 -->
        <div class="tab-panel" v-if="activeTab === 'convert'">
          <div class="card">
            <div class="form-group">
              <label class="form-label">源货币</label>
              <select class="form-select" v-model="convertForm.source">
                <option v-for="opt in currencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">目标货币</label>
              <select class="form-select" v-model="convertForm.target">
                <option v-for="opt in currencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">金额</label>
              <input class="form-input" type="number" v-model.number="convertForm.amount" :min="0" style="width: 200px" />
            </div>
            <button class="btn btn-primary" @click="handleConvert">转换</button>
            <div class="status-msg status-msg-success" v-if="convertResult">
              转换结果<br>
              <small>{{ convertResult.source_amount }} {{ convertResult.source_currency }} = {{ convertResult.target_amount }} {{ convertResult.target_currency }}</small>
            </div>
          </div>
        </div>

        <!-- 税务代理 -->
        <div class="tab-panel" v-if="activeTab === 'agents'">
          <agent-selector />
        </div>

        <!-- 税务报告 -->
        <div class="tab-panel" v-if="activeTab === 'reports'">
          <settlement-table />
        </div>
      </div>

      <!-- 计算弹窗 -->
      <div class="modal-overlay" v-if="showCalcModal">
        <div class="modal-card">
          <h3 style="margin: 0 0 16px">新税务计算</h3>
          <div class="form-group">
            <label class="form-label">产品类型</label>
            <select class="form-select" v-model="calcForm.product_type">
              <option v-for="opt in productTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">金额</label>
            <input class="form-input" type="number" v-model.number="calcForm.amount" :min="0" style="width: 200px" />
          </div>
          <div class="form-group">
            <label class="form-label">卖家地点</label>
            <input class="form-input" v-model="calcForm.seller_country" placeholder="国家" style="width: 100px" />
          </div>
          <div class="form-group">
            <label class="form-label">买家地点</label>
            <input class="form-input" v-model="calcForm.buyer_country" placeholder="国家" style="width: 100px" />
          </div>
          <div class="modal-actions">
            <button class="btn btn-primary" @click="handleCalculate">计算</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import AgentSelector from '@/components/tax/AgentSelector.vue'
import SettlementTable from '@/components/tax/SettlementTable.vue'
import { taxApi } from '@/api/tax'

const activeTab = ref('calc')
const showCalcModal = ref(false)

// 统计数据
const stats = reactive({
  totalIncome: 0,
  totalWithheld: 0,
  totalOwed: 0,
  pendingReports: 0,
})

// 计算历史
const calcHistory = ref<any[]>([])

// 货币转换
const convertForm = reactive({
  source: 'CNY',
  target: 'USD',
  amount: 100,
})
const convertResult = ref<any>(null)

// 税务计算表单
const calcForm = reactive({
  product_type: 'digital',
  amount: 100,
  seller_country: 'US',
  buyer_country: 'CN',
})

const currencyOptions = [
  { label: '人民币 (CNY)', value: 'CNY' },
  { label: '美元 (USD)', value: 'USD' },
  { label: '欧元 (EUR)', value: 'EUR' },
  { label: '英镑 (GBP)', value: 'GBP' },
  { label: '日元 (JPY)', value: 'JPY' },
]

const productTypeOptions = [
  { label: '数字产品', value: 'digital' },
  { label: '实物商品', value: 'physical' },
  { label: '许可证', value: 'license' },
]

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

async function handleConvert() {
  try {
    const res = await taxApi.settlementApi.convertCurrency({
      source_currency: convertForm.source,
      target_currency: convertForm.target,
      amount: convertForm.amount || 0,
    })
    convertResult.value = res.data
  } catch {
    // ignore
  }
}

async function handleCalculate() {
  try {
    const res = await taxApi.settlementApi.calculateTax({
      seller_location: { country: calcForm.seller_country },
      buyer_location: { country: calcForm.buyer_country },
      product_type: calcForm.product_type,
      amount: calcForm.amount || 0,
    })
    calcHistory.value.unshift(res.data)
    showCalcModal.value = false
  } catch {
    // ignore
  }
}
</script>
