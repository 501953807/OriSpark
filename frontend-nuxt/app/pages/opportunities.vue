<template>
  <div class="page-opportunities">
    <h1 class="page-title">合作机会</h1>

    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="opportunities-list">
      <div
        v-for="opp in filteredOpportunities"
        :key="opp.id"
        class="opportunity-card"
      >
        <h3 class="opp-title">{{ opp.title }}</h3>
        <p class="opp-desc">{{ opp.description }}</p>
        <div class="opp-meta">
          <span class="meta-type">{{ oppTypeLabel(opp.type) }}</span>
          <span class="meta-by">by {{ opp.created_by || '平台' }}</span>
        </div>
        <button class="btn-apply">申请入驻</button>
      </div>
    </div>

    <div v-if="!filteredOpportunities.length && !loading" class="empty-state">
      暂无合作机会
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Opportunity } from '~/types/public'

useHead({
  title: '合作机会 — OriSpark',
})

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'operator', label: '运营者需求' },
  { key: 'trader', label: '贸易商采购' },
]

const activeTab = ref('all')
const opportunities = ref<Opportunity[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const res = await fetchOpportunities()
  opportunities.value = (res.data ?? []) as Opportunity[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load opportunities'
} finally {
  loading.value = false
}

const filteredOpportunities = computed(() => {
  if (activeTab.value === 'all') return opportunities.value
  return opportunities.value.filter(o => o.type === activeTab.value)
})

function oppTypeLabel(type: string): string {
  return type === 'operator' ? '运营者' : '贸易商'
}
</script>

<style scoped>
.page-opportunities {
  padding: 32px;
  max-width: 960px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.tab-btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  cursor: pointer;
  color: #374151;
}

.tab-btn.active {
  background: #059669;
  color: #fff;
  border-color: #059669;
}

.opportunities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.opportunity-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.opp-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px;
}

.opp-desc {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 12px;
  line-height: 1.5;
}

.opp-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-type,
.meta-by {
  font-size: 13px;
  color: #6b7280;
}

.btn-apply {
  padding: 8px 20px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-apply:hover {
  background: #047857;
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
