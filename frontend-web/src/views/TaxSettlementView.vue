<template>
  <div class="tax-settlement-view">
    <n-page title="全球税务结算" size="large">
      <!-- 顶部统计 -->
      <n-grid :cols="4" :x-gap="12" responsive="screen" style="margin-bottom: 16px">
        <n-gi>
          <n-statistic label="总收入" :value="stats.totalIncome">
            <template #prefix>
              <span style="color: #52c41a">$</span>
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="已预扣税" :value="stats.totalWithheld">
            <template #prefix>
              <span style="color: #fa8c16">$</span>
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="应纳税" :value="stats.totalOwed">
            <template #prefix>
              <span style="color: #ff4d4f">$</span>
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="待处理报告" :value="stats.pendingReports" />
        </n-gi>
      </n-grid>

      <!-- Tab 切换 -->
      <n-tabs v-model:value="activeTab" type="line">
        <!-- 税务计算 -->
        <n-tab-pane name="calc" tab="税务计算">
          <n-card>
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>实时税务计算</span>
                <n-button type="primary" @click="showCalcModal = true">新计算</n-button>
              </div>
            </template>

            <n-table :rows="calcHistory">
              <template #header-columns>
                <n-th>产品类型</n-th>
                <n-th>金额</n-th>
                <n-th>税率</n-th>
                <n-th>税额</n-th>
                <n-th>司法管辖区</n-th>
                <n-th>时间</n-th>
              </template>
              <template #row-columns="{ row }">
                <n-td>{{ row.product_type }}</n-td>
                <n-td>${{ row.amount.toFixed(2) }}</n-td>
                <n-td>{{ ((row.tax_rate || 0) * 100).toFixed(1) }}%</n-td>
                <n-td>${{ (row.tax_amount || 0).toFixed(2) }}</n-td>
                <n-td>{{ row.tax_jurisdiction || '-' }}</n-td>
                <n-td>{{ formatDate(row.calculated_at) }}</n-td>
              </template>
            </n-table>
          </n-card>
        </n-tab-pane>

        <!-- 货币转换 -->
        <n-tab-pane name="convert" tab="货币转换">
          <n-card>
            <n-space vertical>
              <n-form :model="convertForm" label-placement="left" label-width="100">
                <n-form-item label="源货币">
                  <n-select v-model:value="convertForm.source" :options="currencyOptions" />
                </n-form-item>
                <n-form-item label="目标货币">
                  <n-select v-model:value="convertForm.target" :options="currencyOptions" />
                </n-form-item>
                <n-form-item label="金额">
                  <n-input-number v-model:value="convertForm.amount" :min="0" style="width: 200px" />
                </n-form-item>
              </n-form>
              <n-button type="primary" @click="handleConvert">转换</n-button>
              <n-result
                v-if="convertResult"
                status="success"
                :title="`转换结果`"
                :description="`${convertResult.source_amount} ${convertResult.source_currency} = ${convertResult.target_amount} ${convertResult.target_currency}`"
              />
            </n-space>
          </n-card>
        </n-tab-pane>

        <!-- 税务代理 -->
        <n-tab-pane name="agents" tab="税务代理">
          <agent-selector />
        </n-tab-pane>

        <!-- 税务报告 -->
        <n-tab-pane name="reports" tab="税务报告">
          <settlement-table />
        </n-tab-pane>
      </n-tabs>

      <!-- 计算弹窗 -->
      <n-modal v-model:show="showCalcModal" preset="dialog" title="新税务计算">
        <n-form :model="calcForm" label-placement="left" label-width="120">
          <n-form-item label="产品类型">
            <n-select v-model:value="calcForm.product_type" :options="productTypeOptions" />
          </n-form-item>
          <n-form-item label="金额">
            <n-input-number v-model:value="calcForm.amount" :min="0" style="width: 200px" />
          </n-form-item>
          <n-form-item label="卖家地点">
            <n-input v-model:value="calcForm.seller_country" placeholder="国家" style="width: 100px" />
          </n-form-item>
          <n-form-item label="买家地点">
            <n-input v-model:value="calcForm.buyer_country" placeholder="国家" style="width: 100px" />
          </n-form-item>
        </n-form>
        <template #action>
          <n-button type="primary" @click="handleCalculate">计算</n-button>
        </template>
      </n-modal>
    </n-page>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { NPage, NGrid, NGi, NStatistic, NTabs, NTabPane, NCard, NTable, NTh, NTd, NButton, NSpace, NForm, NFormItem, NSelect, NInput, NInputNumber, NModal, NResult } from 'naive-ui'
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
