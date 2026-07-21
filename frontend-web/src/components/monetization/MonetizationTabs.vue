<!-- MonetizationTabs — 变现路径子Tab导航

Used in: ListingDetailView as sub-navigation for POD/Crowdfunding/IP/Revenue/Orders
Each tab shows its respective panel component.
-->
<template>
  <div class="monetization-tabs">
    <!-- Tab header -->
    <div class="tab-header">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <!-- POD 发布 -->
      <PublicationPanel
        v-if="activeTab === 'publication' && listingId"
        :listing-id="listingId"
        @publish="emit('publish', $event)"
      />

      <!-- 众筹 -->
      <CampaignPanel
        v-if="activeTab === 'campaign' && listingId"
        :listing-id="listingId"
        @create-campaign="emit('create-campaign', $event)"
      />

      <!-- IP 授权 -->
      <LicensePanel
        v-if="activeTab === 'license' && listingId"
        :listing-id="listingId"
        @create-license="emit('create-license', $event)"
      />

      <!-- 收入 -->
      <RevenuePanel
        v-if="activeTab === 'revenue' && listingId"
        :listing-id="listingId"
      />

      <!-- 订单 -->
      <OrderPanel
        v-if="activeTab === 'order' && listingId"
        :listing-id="listingId"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import PublicationPanel from './PublicationPanel.vue'
import CampaignPanel from './CampaignPanel.vue'
import LicensePanel from './LicensePanel.vue'
import RevenuePanel from './RevenuePanel.vue'
import OrderPanel from './OrderPanel.vue'

interface Props {
  listingId: string
  active?: string
  counts?: {
    publication?: number
    campaign?: number
    license?: number
    revenue?: number
    order?: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  active: 'publication',
  counts: () => ({}),
})

const emit = defineEmits<{
  (e: 'update:active', val: string): void
  (e: 'publish', id: string): void
  (e: 'create-campaign', data: any): void
  (e: 'create-license', data: any): void
}>()

const tabs = [
  { key: 'publication', icon: '🖨️', label: 'POD 发布', count: props.counts.publication },
  { key: 'campaign', icon: '🚀', label: '众筹', count: props.counts.campaign },
  { key: 'license', icon: '📜', label: 'IP 授权', count: props.counts.license },
  { key: 'revenue', icon: '💰', label: '收入', count: props.counts.revenue },
  { key: 'order', icon: '📋', label: '订单', count: props.counts.order },
]

const activeTab = ref(props.active)

watchEffect(() => {
  activeTab.value = props.active
  emit('update:active', props.active)
})
</script>

<style scoped>
.monetization-tabs {
  margin-top: 16px;
}

.tab-header {
  display: flex;
  gap: 2px;
  border-bottom: 2px solid var(--border);
  margin-bottom: 16px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: .85rem;
  font-weight: 600;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
}

.tab-btn:hover {
  color: var(--accent);
}

.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab-icon {
  font-size: 1rem;
}

.tab-count {
  background: var(--muted-bg);
  padding: 0 6px;
  border-radius: 100px;
  font-size: .65rem;
  font-weight: 700;
}

.tab-content {
  padding-top: 8px;
}
</style>
