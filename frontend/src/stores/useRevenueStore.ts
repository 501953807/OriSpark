import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RevenueSummaryResponse, DiversityIndexResponse } from '@/types/revenue'
import { revenueApi } from '@/api/revenue'

export const useRevenueStore = defineStore('revenue', () => {
  const summary = ref<RevenueSummaryResponse | null>(null)
  const diversity = ref<DiversityIndexResponse | null>(null)
  const loading = ref(false)

  async function fetch(userId: string, months = 12) {
    loading.value = true
    try {
      const [sumRes, divRes] = await Promise.all([
        revenueApi.getSummary(userId, months),
        revenueApi.getDiversity(userId, months),
      ])
      summary.value = sumRes.data.data as RevenueSummaryResponse
      diversity.value = divRes.data.data as DiversityIndexResponse
    } catch (e) {
      console.error('fetch revenue data failed:', e)
    } finally {
      loading.value = false
    }
  }

  return { summary, diversity, loading, fetch }
})
