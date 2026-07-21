<script setup lang="ts">
import { ref } from 'vue'

interface Batch {
  id: string
  batch_number: string
  product_name: string
  start_date?: string
  status: 'planned' | 'in_production' | 'inspecting' | 'done' | 'shipped'
  planned_quantity: number
  produced_quantity: number
  sold_quantity?: number
}

const props = defineProps<{ batches?: Batch[] }>()

const statusLabels: Record<string, string> = {
  planned: '计划中', in_production: '生产中', inspecting: '质检中', done: '已完成', shipped: '已发货',
}
const statusColors: Record<string, string> = {
  planned: '#9ca3af', in_production: '#f59e0b', inspecting: '#8b5cf6', done: '#22c55e', shipped: '#06b6d4',
}

const onViewDetail = (batchNumber: string) => window.alert(`详情: ${batchNumber}`)
const onQualityCheck = (batchNumber: string) => window.alert(`质检: ${batchNumber}`)
</script>

<template>
  <div class="production-batch-panel">
    <div class="panel-header">
      <h3>生产批次</h3>
      <button class="btn btn-primary btn-sm">+ 新建批次</button>
    </div>
    <table v-if="batches?.length" class="batch-table">
      <thead><tr><th>批次号</th><th>产品</th><th>开始日期</th><th>状态</th><th>计划产量</th><th>已完成</th><th>已售</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="batch in batches" :key="batch.id">
          <td>{{ batch.batch_number }}</td><td>{{ batch.product_name }}</td>
          <td>{{ batch.start_date || '-' }}</td>
          <td><span class="status-badge" :style="{ backgroundColor: statusColors[batch.status] + '22', color: statusColors[batch.status] }">{{ statusLabels[batch.status] }}</span></td>
          <td>{{ batch.planned_quantity }}</td><td>{{ batch.produced_quantity }}</td><td>{{ batch.sold_quantity || 0 }}</td>
          <td class="actions"><button class="btn-link" @click="onViewDetail(batch.batch_number)">详情</button><button class="btn-link" @click="onQualityCheck(batch.batch_number)">质检</button></td>
        </tr>
      </tbody>
    </table>
    <div v-if="!batches?.length" class="empty-state">暂无生产批次</div>
  </div>
</template>

<style scoped>
.production-batch-panel { padding: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.batch-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.batch-table th, .batch-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; text-align: left; }
.batch-table th { background: #f9fafb; font-weight: 600; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.actions { display: flex; gap: 8px; }
.empty-state { padding: 32px; text-align: center; color: #9ca3af; }
.btn-sm { padding: 4px 12px; font-size: 13px; }
</style>
