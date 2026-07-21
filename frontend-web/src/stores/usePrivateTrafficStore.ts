import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/privateTraffic'
import type { SubscriptionLink, FanCommunity, FunnelSummary } from '@/types/privateTraffic'

export const usePrivateTrafficStore = defineStore('privateTraffic', () => {
  const subscriptions = ref<SubscriptionLink[]>([])
  const communities = ref<FanCommunity[]>([])
  const funnel = ref<FunnelSummary | null>(null)
  const loading = ref(false)

  async function loadAll() {
    loading.value = true
    try {
      const [subs, comms, fun] = await Promise.all([
        api.listSubscriptions(),
        api.listCommunities(),
        api.getFunnelSummary(),
      ])
      subscriptions.value = subs
      communities.value = comms
      funnel.value = fun
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    subscriptions,
    communities,
    funnel,
    loadAll,
  }
})
