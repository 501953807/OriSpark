<template>
  <div class="page-contract-detail">
    <div class="container">
      <NuxtLink to="/contracts" class="back-link">← 返回合约列表</NuxtLink>
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else-if="contract">
        <div class="card-header">
          <h1 class="contract-title">{{ contract.title }}</h1>
          <span class="status-badge" :class="'status-' + contract.status">
            {{ statusLabel(contract.status) }}
          </span>
        </div>
        <p class="contract-desc">{{ contract.description }}</p>
        <div class="contract-meta">
          <span class="meta-item">类型: {{ contractTypeLabel(contract.contract_type) }}</span>
          <span class="meta-item">金额: {{ contract.currency }} {{ contract.total_amount?.toLocaleString() ?? '—' }}</span>
          <span class="meta-item">范围: {{ contract.scopeUsage }} / {{ contract.scopeGeography }}</span>
        </div>
        <div class="card-actions">
          <a href="https://studio.orispark.local" target="_blank" class="btn-cta">
            在 OriStudio 中操作
          </a>
        </div>
      </div>
      <div v-else class="empty-state">未找到该合约</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Contract } from '~/types/public'
import { fetchPublicContracts } from '~/composables/usePublicApi'

const route = useRoute()
const contract = ref<Contract | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function loadContract() {
  const id = route.params.id as string
  if (!id) return
  loading.value = true
  error.value = null
  try {
    const res = await fetchPublicContracts()
    const found = (res ?? []).find((c: Contract) => c.id === id)
    contract.value = found ?? null
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load contract'
  } finally {
    loading.value = false
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿', listed: '挂牌中', active: '活跃',
    escrowed: '托管中', insured: '已投保', executing: '执行中',
    completed: '已完成', dispute: '争议中', resolved: '已解决',
    refunded: '已退款', cancelled: '已取消',
  }
  return labels[status] ?? status
}

function contractTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    exclusive_license: '独占许可', non_exclusive_license: '非独占许可',
    transfer: '转让', commission: '委托创作',
  }
  return labels[type] ?? type
}

onMounted(loadContract)
</script>

<style scoped>
.page-contract-detail {
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 24px;
  color: #6b7280;
  text-decoration: none;
  font-size: 14px;
}

.back-link:hover {
  color: #374151;
}

.contract-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-listed { background: #fef3c7; color: #92400e; }
.status-active { background: #d1fae5; color: #065f46; }
.status-executing { background: #dbeafe; color: #1e40af; }
.status-completed { background: #e5e7eb; color: #374151; }
.status-dispute { background: #fee2e2; color: #991b1b; }

.contract-desc {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 20px;
}

.contract-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.meta-item {
  font-size: 13px;
  color: #6b7280;
}

.card-actions {
  margin-top: 24px;
}

.btn-cta {
  display: inline-block;
  padding: 10px 20px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.btn-cta:hover {
  background: #047857;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}
</style>
