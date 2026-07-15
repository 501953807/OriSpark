import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import type { RevenueSummary, TrendsSummary, DashboardStats, RecentWork } from '@/api/dashboard'
import { useAppStore } from './useAppStore'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats | null>(null)
  const recentWorks = ref<RecentWork[]>([])
  const loading = ref(false)

  // Revenue data
  const revenue = ref<RevenueSummary | null>(null)

  // Trend data
  const trends = ref<TrendsSummary | null>(null)

  // ---------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------

  async function fetchStats() {
    loading.value = true
    try {
      const res = await dashboardApi.stats()
      stats.value = res.data.data
      recentWorks.value = stats.value.recent_works || []
      // 同步到全局
      const appStore = useAppStore()
      appStore.setStats({
        total_works: stats.value.total_works,
        total_notarized: stats.value.total_notarized,
        infringement_alerts: stats.value.infringement_alerts,
      })
    } finally {
      loading.value = false
    }
  }

  async function fetchRecent() {
    try {
      const res = await dashboardApi.recent()
      recentWorks.value = res.data.data
    } catch (e) {
      console.error('fetchRecent failed:', e)
    }
  }

  async function fetchRevenue() {
    try {
      const res = await dashboardApi.revenue()
      revenue.value = res.data.data
    } catch (e) {
      console.error('fetchRevenue failed:', e)
    }
  }

  async function fetchTrends() {
    try {
      const res = await dashboardApi.trends()
      trends.value = res.data.data
    } catch (e) {
      console.error('fetchTrends failed:', e)
    }
  }

  async function refreshAll() {
    loading.value = true
    try {
      await Promise.all([fetchStats(), fetchRevenue(), fetchTrends()])
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    recentWorks,
    loading,
    revenue,
    trends,
    fetchStats,
    fetchRecent,
    fetchRevenue,
    fetchTrends,
    refreshAll,
  }
})
