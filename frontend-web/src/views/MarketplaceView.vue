<script setup lang="ts">
import { ref, computed } from 'vue'
import BatchListingPanel from '@/components/marketplace/BatchListingPanel.vue'
import NegotiationChat from '@/components/marketplace/NegotiationChat.vue'
import SettlementDashboard from '@/components/marketplace/SettlementDashboard.vue'
import WithdrawalForm from '@/components/marketplace/WithdrawalForm.vue'
import ContractPreview from '@/components/marketplace/ContractPreview.vue'
import FeeConfigPanel from '@/components/marketplace/FeeConfigPanel.vue'
import ListingSearch from '@/components/marketplace/ListingSearch.vue'
import { supplyApi } from '@/api/supply'
import type { ListingDetail } from '@/types/supply'

const activeTab = ref('listings')

const tabs = [
  { key: 'listings', label: ' listings', icon: '📋' },
  { key: 'matchmaking', label: '需求撮合', icon: '🤝' },
  { key: 'negotiation', label: '议价中心', icon: '💬' },
  { key: 'settlement', label: 'POD 结算', icon: '📊' },
  { key: 'commission', label: '佣金提现', icon: '💰' },
  { key: 'contract', label: '授权合同', icon: '📄' },
  { key: 'fees', label: '费率配置', icon: '⚙️' },
] as const

const listings = ref<ListingDetail[]>([])
const loading = ref(true)

async function loadListings() {
  loading.value = true
  try {
    const res = await supplyApi.listings({ page: 1, page_size: 20 })
    listings.value = (res.data as ListingDetail[]) || []
  } catch { /* handled */ } finally { loading.value = false }
}

loadListings()
</script>

<template>
  <div class="marketplace-view">
    <h2>商业撮合交易</h2>
    <p class="subtitle">IP 授权、议价撮合、POD 结算与佣金管理</p>

    <!-- Tab navigation -->
    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['tab', { active: activeTab === t.key }]"
        @click="activeTab = t.key"
      >
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <!-- Listings tab -->
    <div v-if="activeTab === 'listings'" class="section">
      <div class="section-header">
        <h3>商品列表</h3>
        <BatchListingPanel :listings="listings" @refresh="loadListings" />
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="listings.length === 0" class="empty-state">暂无上架商品</div>
      <div v-else class="listing-grid">
        <div v-for="l in listings" :key="l.id" class="listing-card card">
          <h4>{{ l.title }}</h4>
          <p class="desc">{{ l.description?.slice(0, 80) }}...</p>
          <div class="listing-meta">
            <span class="price">¥{{ l.asking_price_yuan?.toLocaleString() ?? '--' }}</span>
            <span class="status-chip" :class="l.status">{{ l.status }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Matchmaking tab -->
    <div v-if="activeTab === 'matchmaking'" class="section">
      <ListingSearch />
    </div>

    <!-- Negotiation tab -->
    <div v-if="activeTab === 'negotiation'" class="section">
      <NegotiationChat negotiation-id="demo-negotiation-id" @updated="() => {}" />
    </div>

    <!-- Settlement tab -->
    <div v-if="activeTab === 'settlement'" class="section">
      <SettlementDashboard />
    </div>

    <!-- Commission tab -->
    <div v-if="activeTab === 'commission'" class="section">
      <WithdrawalForm />
    </div>

    <!-- Contract tab -->
    <div v-if="activeTab === 'contract'" class="section">
      <ContractPreview license-id="demo-license-id" />
    </div>

    <!-- Fees tab -->
    <div v-if="activeTab === 'fees'" class="section">
      <FeeConfigPanel />
    </div>
  </div>
</template>

<style scoped>
.marketplace-view { max-width: 1200px; }
.subtitle { color: var(--muted); margin-bottom: 16px; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 20px; overflow-x: auto; }
.tab { padding: 10px 16px; border: none; background: none; cursor: pointer; font-size: 0.9rem; white-space: nowrap; opacity: 0.6; transition: opacity 0.2s; }
.tab:hover { opacity: 0.8; }
.tab.active { opacity: 1; border-bottom: 2px solid var(--primary); }
.section { margin-top: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.listing-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.listing-card { padding: 16px; }
.desc { font-size: 0.85rem; color: var(--muted); margin: 8px 0; }
.listing-meta { display: flex; justify-content: space-between; align-items: center; }
.price { font-size: 1.1rem; font-weight: 600; color: #059669; }
.status-chip { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; background: #f3f4f6; }
.empty-state { text-align: center; padding: 40px; color: var(--muted); }
.loading { text-align: center; padding: 40px; color: var(--muted); }
</style>
