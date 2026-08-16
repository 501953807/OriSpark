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
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--m-shadow-md);
  transition: box-shadow 0.2s;
}
.contract-card:hover {
  box-shadow: rgba(46, 38, 61, 0.2) 0px 4px 10px 0px;
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
  color: var(--m-on-surface);
  margin: 0;
}

.status-badge {
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-listed { background: var(--m-warning-light); color: rgb(160, 100, 0); }
.status-active { background: var(--m-success-light); color: rgb(40, 120, 0); }
.status-executing { background: rgba(85, 133, 255, 0.12); color: rgb(40, 80, 180); }
.status-completed { background: var(--m-grey-100); color: var(--m-grey-700); }
.status-dispute { background: var(--m-error-light); color: rgb(180, 40, 40); }

.contract-desc {
  font-size: 14px;
  color: rgba(46, 38, 61, 0.6);
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
  color: var(--m-grey-500);
}

.card-actions {
  display: flex;
  gap: 12px;
}

.btn-detail,
.btn-cta {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-detail {
  background: transparent;
  color: var(--m-success);
  border: 1px solid var(--m-success);
}

.btn-detail:hover {
  background: rgba(86, 202, 0, 0.06);
}

.btn-cta {
  background: var(--m-primary);
  color: #fff;
  border: none;
}

.btn-cta:hover {
  background: rgb(110, 57, 220);
}
</style>
