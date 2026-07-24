<template>
  <n-card title="税务报告">
    <template #header-extra>
      <n-button type="primary" size="small" @click="showGenerate = true">生成报告</n-button>
    </template>

    <n-data-table :columns="columns" :data="reports" :loading="loading" />

    <n-modal v-model:show="showGenerate" preset="dialog" title="生成税务报告">
      <n-form :model="reportForm" label-placement="left" label-width="80">
        <n-form-item label="参与者 ID">
          <n-input v-model:value="reportForm.participant_id" />
        </n-form-item>
        <n-form-item label="周期">
          <n-input v-model:value="reportForm.period" placeholder="2024-08" />
        </n-form-item>
        <n-form-item label="货币">
          <n-select v-model:value="reportForm.currency" :options="currencyOptions" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showGenerate = false">取消</n-button>
          <n-button type="primary" @click="handleGenerate">生成</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { NCard, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, NSpace } from 'naive-ui'
import { useMessage } from 'naive-ui'
import { taxApi } from '@/api/tax'

const message = useMessage()
const loading = ref(false)
const reports = ref<any[]>([])
const showGenerate = ref(false)

const reportForm = reactive({
  participant_id: '',
  period: '',
  currency: 'CNY',
})

const currencyOptions = [
  { label: '人民币 (CNY)', value: 'CNY' },
  { label: '美元 (USD)', value: 'USD' },
  { label: '欧元 (EUR)', value: 'EUR' },
]

const columns = [
  { title: 'ID', key: 'id' },
  { title: '周期', key: 'report_period' },
  { title: '总收入', key: 'total_income', render(row) { return `$${row.total_income.toFixed(2)}` } },
  { title: '预扣税', key: 'total_tax_withheld', render(row) { return `$${row.total_tax_withheld.toFixed(2)}` } },
  { title: '应纳税', key: 'total_tax_owed', render(row) { return `$${row.total_tax_owed.toFixed(2)}` } },
  { title: '状态', key: 'status' },
]

async function fetchReports() {
  if (!reportForm.participant_id) return
  loading.value = true
  try {
    const res = await taxApi.taxAgentApi.listReports(reportForm.participant_id)
    reports.value = res.data || []
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  try {
    await taxApi.taxAgentApi.createReport(reportForm)
    message.success('报告已生成')
    showGenerate.value = false
    fetchReports()
  } catch {
    message.error('生成失败')
  }
}
</script>
