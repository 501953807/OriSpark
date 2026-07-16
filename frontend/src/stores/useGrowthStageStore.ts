import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/growthStage'
import type { ProgressDashboard } from '@/types/growthStage'

export const useGrowthStageStore = defineStore('growthStage', () => {
  const dashboard = ref<ProgressDashboard | null>(null)
  const loading = ref(false)

  async function loadDashboard() {
    loading.value = true
    try {
      dashboard.value = await api.getDashboard()
    } finally {
      loading.value = false
    }
  }

  async function updateMetrics(data: Parameters<typeof api.updateMetrics>[0]) {
    dashboard.value = await api.updateMetrics(data)
    return dashboard.value
  }

  return {
    loading,
    dashboard,
    loadDashboard,
    updateMetrics,
  }
})
