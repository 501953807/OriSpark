<template>
  <div class="contract-card">
    <div class="card-header">
      <h3 class="contract-title">{{ contract.title }}</h3>
      <span class="status-badge" :class="'status-' + contract.status">
        {{ statusLabel(contract.status) }}
      </span>
    </div>
    <p class="contract-desc">{{ contract.description }}</p>
    <div class="contract-meta">
      <span class="meta-item">类型: {{ contractTypeLabel(contract.contract_type) }}</span>
      <span class="meta-item">金额: {{ contract.currency }} {{ contract.total_amount.toLocaleString() }}</span>
      <span class="meta-item">范围: {{ contract.scopeUsage }} / {{ contract.scopeGeography }}</span>
    </div>
    <div class="card-actions">
      <NuxtLink :to="`/contracts/${contract.id}`" class="btn-detail">
        查看详情
      </NuxtLink>
      <a href="https://studio.orispark.local" target="_blank" class="btn-cta">
        在 OriStudio 中操作
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Contract } from '~/types/public'

defineProps<{
  contract: Contract
}>()

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    listed: '挂牌中',
    active: '活跃',
    escrowed: '托管中',
    insured: '已投保',
    executing: '执行中',
    completed: '已完成',
    dispute: '争议中',
    resolved: '已解决',
    refunded: '已退款',
    cancelled: '已取消',
  }
  return labels[status] ?? status
}

function contractTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    exclusive_license: '独占许可',
    non_exclusive_license: '非独占许可',
    transfer: '转让',
    commission: '委托创作',
  }
  return labels[type] ?? type
}
</script>

<style scoped>
.contract-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.contract-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-listed { background: #fef3c7; color: #92400e; }
.status-active { background: #d1fae5; color: #065f46; }
.status-executing { background: #dbeafe; color: #1e40af; }
.status-completed { background: #e5e7eb; color: #374151; }
.status-dispute { background: #fee2e2; color: #991b1b; }

.contract-desc {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 12px;
  line-height: 1.5;
}

.contract-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.meta-item {
  font-size: 13px;
  color: #6b7280;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.btn-detail,
.btn-cta {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.btn-detail {
  background: #fff;
  color: #059669;
  border: 1px solid #059669;
}

.btn-detail:hover {
  background: #ecfdf5;
}

.btn-cta {
  background: #059669;
  color: #fff;
  border: none;
}

.btn-cta:hover {
  background: #047857;
}
</style>
