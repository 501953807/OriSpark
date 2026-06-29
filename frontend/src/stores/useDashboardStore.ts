import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import { useAppStore } from './useAppStore'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<any>(null)
  const recentWorks = ref<any[]>([])
  const loading = ref(false)

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
    const res = await dashboardApi.recent()
    recentWorks.value = res.data.data
  }

  return {
    stats,
    recentWorks,
    loading,
    fetchStats,
    fetchRecent,
  }
})
