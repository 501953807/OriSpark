<template>
  <div class="card">
    <div class="modal-header">
      <h3>税务报告</h3>
      <button class="btn btn-sm btn-primary" @click="showGenerate = true">生成报告</button>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>周期</th>
          <th>总收入</th>
          <th>预扣税</th>
          <th>应纳税</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody v-if="!loading">
        <tr v-for="row in reports" :key="row.id">
          <td>{{ row.id }}</td>
          <td>{{ row.report_period }}</td>
          <td>${{ (row.total_income as number).toFixed(2) }}</td>
          <td>${{ (row.total_tax_withheld as number).toFixed(2) }}</td>
          <td>${{ (row.total_tax_owed as number).toFixed(2) }}</td>
          <td>{{ row.status }}</td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr><td colspan="6" class="text-center">加载中...</td></tr>
      </tbody>
    </table>

    <div v-if="showGenerate" class="modal-overlay" @click.self="showGenerate = false">
      <div class="modal-card">
        <div class="modal-header"><h3>生成税务报告</h3></div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">参与者 ID</label>
            <input class="form-input" v-model="reportForm.participant_id" />
          </div>
          <div class="form-group">
            <label class="form-label">周期</label>
            <input class="form-input" v-model="reportForm.period" placeholder="2024-08" />
          </div>
          <div class="form-group">
            <label class="form-label">货币</label>
            <select class="form-select" v-model="reportForm.currency">
              <option value="CNY">人民币 (CNY)</option>
              <option value="USD">美元 (USD)</option>
              <option value="EUR">欧元 (EUR)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showGenerate = false">取消</button>
          <button class="btn btn-primary" @click="handleGenerate">生成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { taxApi } from '@/api/tax'

const loading = ref(false)
const reports = ref<any[]>([])
const showGenerate = ref(false)
const errorMsg = ref('')
const participantId = ref('')

const reportForm = reactive({
  participant_id: '',
  period: new Date().toISOString().slice(0, 7),
  currency: 'CNY',
})

async function fetchReports() {
  if (!participantId.value) return
  loading.value = true
  try {
    const res = await taxApi.taxAgentApi.listReports(participantId.value)
    reports.value = (res.data?.data ?? []) as any[]
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (!reportForm.period) return
  try {
    await taxApi.taxAgentApi.createReport(reportForm)
    showGenerate.value = false
    reportForm.period = new Date().toISOString().slice(0, 7)
    await fetchReports()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '生成失败'
  }
}

onMounted(fetchReports)
</script>
