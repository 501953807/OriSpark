<script setup lang="ts">
import { ref, computed } from 'vue'

interface Campaign {
  id: string
  brand_name: string
  title: string
  description?: string
  budget_min?: number
  budget_max?: number
  currency?: string
  status: 'draft' | 'negotiating' | 'in_progress' | 'delivered' | 'closed'
  deadline?: string
}

const props = defineProps<{ campaigns?: Campaign[] }>()
const viewMode = ref<'card' | 'table'>('card')
const showForm = ref(false)
const editingCampaign = ref<Campaign | null>(null)

const statusLabels: Record<string, string> = {
  draft: '草稿', negotiating: '谈判中', in_progress: '进行中', delivered: '已交付', closed: '已关闭',
}
const statusColors: Record<string, string> = {
  draft: '#9ca3af', negotiating: '#f59e0b', in_progress: '#3b82f6', delivered: '#8b5cf6', closed: '#6b7280',
}

function openEdit(camp: Campaign) { editingCampaign.value = camp; showForm.value = true }
function progressPercent(camp: Campaign) {
  return camp.status === 'closed' ? 100 : camp.status === 'delivered' ? 75 : camp.status === 'in_progress' ? 40 : camp.status === 'negotiating' ? 20 : 0
}
</script>

<template>
  <div class="brand-campaign-panel">
    <div class="panel-header">
      <h3>品牌合作</h3>
      <div class="controls">
        <div class="view-toggle">
          <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">卡片</button>
          <button :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'">列表</button>
        </div>
        <button class="btn btn-primary btn-sm">+ 新建合作</button>
      </div>
    </div>

    <div v-if="viewMode === 'card'" class="campaign-cards">
      <div v-for="camp in campaigns" :key="camp.id" class="campaign-card">
        <div class="card-header">
          <h4>{{ camp.brand_name }}</h4>
          <span class="status-badge" :style="{ backgroundColor: statusColors[camp.status] + '22', color: statusColors[camp.status] }">{{ statusLabels[camp.status] }}</span>
        </div>
        <p class="campaign-title">{{ camp.title }}</p>
        <div class="card-meta">
          <span v-if="camp.deadline">截止: {{ camp.deadline }}</span>
          <span v-if="camp.budget_min != null">{{ camp.currency || 'CNY' }} {{ camp.budget_min }}–{{ camp.budget_max }}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" :style="{ width: progressPercent(camp) + '%' }"></div></div>
        <div class="card-actions">
          <button @click="openEdit(camp)">编辑</button>
          <button class="btn-danger" @click="$emit('delete', camp.id)">删除</button>
        </div>
      </div>
      <div v-if="!campaigns?.length" class="empty-state">暂无品牌合作项目</div>
    </div>

    <table v-if="viewMode === 'table' && campaigns?.length" class="campaign-table">
      <thead><tr><th>品牌</th><th>标题</th><th>状态</th><th>截止日期</th><th>预算</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="camp in campaigns" :key="camp.id">
          <td>{{ camp.brand_name }}</td><td>{{ camp.title }}</td>
          <td><span class="status-badge" :style="{ backgroundColor: statusColors[camp.status] + '22', color: statusColors[camp.status] }">{{ statusLabels[camp.status] }}</span></td>
          <td>{{ camp.deadline || '-' }}</td>
          <td>{{ camp.budget_min ? `${camp.currency || 'CNY'} ${camp.budget_min}` : '-' }}</td>
          <td><button @click="openEdit(camp)">编辑</button></td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="form-overlay">
      <div class="form-card">
        <h4>编辑合作</h4>
        <p>品牌: {{ editingCampaign?.brand_name }}</p>
        <button @click="showForm = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.brand-campaign-panel { padding: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.controls { display: flex; gap: 8px; align-items: center; }
.view-toggle button { padding: 4px 12px; border: 1px solid #d1d5db; background: #fff; cursor: pointer; }
.view-toggle button:first-child { border-radius: 4px 0 0 4px; }
.view-toggle button:last-child { border-radius: 0 4px 4px 0; }
.view-toggle button.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.campaign-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.campaign-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-header h4 { margin: 0; font-size: 16px; }
.campaign-title { margin: 0 0 8px; font-size: 14px; color: #6b7280; }
.card-meta { display: flex; gap: 12px; font-size: 12px; color: #9ca3af; margin-bottom: 8px; }
.progress-bar { height: 4px; background: #e5e7eb; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; transition: width 0.3s; }
.card-actions { display: flex; gap: 8px; margin-top: 12px; }
.card-actions button { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.card-actions .btn-danger { color: #ef4444; border-color: #fecaca; }
.campaign-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.campaign-table th, .campaign-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; text-align: left; }
.campaign-table th { background: #f9fafb; font-weight: 600; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.empty-state { grid-column: 1/-1; padding: 32px; text-align: center; color: #9ca3af; }
.form-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.form-card { background: #fff; border-radius: 8px; padding: 24px; min-width: 300px; }
.btn-sm { padding: 4px 12px; font-size: 13px; }
</style>
