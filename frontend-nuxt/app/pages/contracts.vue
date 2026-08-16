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
definePageMeta({ layout: 'materio-topnav' })
import { ref, onMounted, watch } from 'vue'
import type { Contract } from '~/types/public'
import { fetchPublicContracts } from '~/composables/usePublicApi'

useHead({
  title: '合约市场 — OriSpark',
})

const selectedType = ref('')
const selectedStatus = ref('')
const contracts = ref<Contract[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function loadContracts() {
  loading.value = true
  error.value = null
  try {
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
}

onMounted(loadContracts)
watch([selectedType, selectedStatus], loadContracts)
</script>

<style scoped>
.page-contracts {
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--m-on-surface);
  padding: 0 24px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 0 24px;
}

.category-select {
  padding: 8px 14px;
  border: 1px solid var(--m-border);
  border-radius: 6px;
  font-size: 14px;
  background: #FFFFFF;
  color: var(--m-on-surface);
  font-family: inherit;
}

.contracts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 24px;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--m-grey-500);
}

.error-state {
  color: var(--m-error);
}
</style>
