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
definePageMeta({ layout: 'materio-topnav' })
import { ref, onMounted, computed } from 'vue'
import type { Opportunity } from '~/types/public'
import { fetchOpportunities } from '~/composables/usePublicApi'

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

async function loadOpportunities() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchOpportunities()
    opportunities.value = (res.data ?? []) as Opportunity[]
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load opportunities'
  } finally {
    loading.value = false
  }
}

onMounted(loadOpportunities)

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
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--m-on-surface);
  padding: 0 24px;
}

.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  padding: 0 24px;
  border-bottom: 1px solid var(--m-border);
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  background: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--m-grey-500);
  font-family: inherit;
  transition: all 0.2s;
}

.tab-btn.active {
  color: var(--m-primary);
  border-bottom-color: var(--m-primary);
  font-weight: 600;
}

.opportunities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 24px;
}

.opportunity-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: 20px;
  transition: box-shadow 0.2s;
}

.opportunity-card:hover {
  box-shadow: rgba(46, 38, 61, 0.2) 0px 4px 10px 0px;
}

.opp-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--m-on-surface);
}

.opp-desc {
  font-size: 14px;
  color: var(--m-grey-700);
  margin: 0 0 12px;
  line-height: 1.5;
}

.opp-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.meta-type,
.meta-by {
  font-size: 13px;
  color: var(--m-grey-500);
}

.btn-apply {
  padding: 8px 20px;
  background: var(--m-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.btn-apply:hover {
  background: rgb(110, 57, 220);
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
