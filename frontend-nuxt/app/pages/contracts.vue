<template>
  <div class="page-contracts">
    <h1 class="page-title">合约市场公开页</h1>

    <div class="filter-bar">
      <select v-model="selectedType" class="category-select">
        <option value="">全部类型</option>
        <option value="exclusive_license">独占许可</option>
        <option value="non_exclusive_license">非独占许可</option>
        <option value="transfer">转让</option>
        <option value="commission">委托创作</option>
      </select>
      <select v-model="selectedStatus" class="category-select">
        <option value="">全部状态</option>
        <option value="listed">挂牌中</option>
        <option value="active">活跃</option>
        <option value="executing">执行中</option>
        <option value="completed">已完成</option>
      </select>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="contracts-list">
      <ContractCard v-for="contract in contracts" :key="contract.id" :contract="contract" />
    </div>

    <div v-if="!contracts.length && !loading" class="empty-state">
      暂无合约
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Contract } from '~/types/public'

useHead({
  title: '合约市场 — OriSpark',
})

const selectedType = ref('')
const selectedStatus = ref('')
const contracts = ref<Contract[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const params: Record<string, string> = {}
  if (selectedType.value) params.contract_type = selectedType.value
  if (selectedStatus.value) params.status = selectedStatus.value
  const res = await fetchPublicContracts(params)
  contracts.value = (res ?? []) as Contract[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load contracts'
} finally {
  loading.value = false
}
</script>

<style scoped>
.page-contracts {
  padding: 32px;
  max-width: 960px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.category-select {
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}

.contracts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}
</style>
