<template>
  <section class="contracts-section">
    <div class="section-header">
      <h2 class="section-title">最新合约挂牌</h2>
      <NuxtLink to="/contracts" class="view-all">查看全部 →</NuxtLink>
    </div>
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="contracts-list">
      <ContractCard v-for="contract in recentContracts" :key="contract.id" :contract="contract" />
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Contract } from '~/types/public'
import ContractCard from './ContractCard.vue'

const contracts = ref<Contract[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const res = await fetchPublicContracts({ limit: '5' })
  contracts.value = (res ?? []) as Contract[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load contracts'
} finally {
  loading.value = false
}

const recentContracts = computed(() => contracts.value.slice(0, 5))
</script>

<style scoped>
.contracts-section {
  padding: 48px 32px;
  background: #f9fafb;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 32px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.view-all {
  color: #059669;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.contracts-list {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state,
.error-state {
  text-align: center;
  color: #6b7280;
  padding: 48px 0;
}
</style>
