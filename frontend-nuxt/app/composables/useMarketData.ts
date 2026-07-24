import type { DashboardStats, MarketTrend } from '~/types/public'
import { fetchDashboardStats, fetchMarketTrends } from './usePublicApi'

export function useMarketData() {
  const stats = ref<DashboardStats | null>(null)
  const trends = ref<MarketTrend[] | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadStats() {
    loading.value = true
    error.value = null
    try {
      const res = await fetchDashboardStats()
      stats.value = (res ?? null) as DashboardStats | null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load dashboard stats'
    } finally {
      loading.value = false
    }
  }

  async function loadTrends(period: string = 'monthly') {
    loading.value = true
    error.value = null
    try {
      const res = await fetchMarketTrends(period)
      trends.value = (res ?? null) as MarketTrend[] | null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load market trends'
    } finally {
      loading.value = false
    }
  }

  return { stats, trends, loading, error, loadStats, loadTrends }
}
