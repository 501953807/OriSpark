import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RiskWarning, RiskCheckRequest } from '@/types/risk_warning'
import { riskWarningApi } from '@/api/risk_warning'

export const useRiskWarningStore = defineStore('riskWarning', () => {
  const warnings = ref<RiskWarning[]>([])
  const loading = ref(false)

  async function check(data: Record<string, unknown>) {
    loading.value = true
    try {
      const res = await riskWarningApi.check(data as RiskCheckRequest)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchByWork(workId: string) {
    const res = await riskWarningApi.getByWork(workId)
    warnings.value = res.data.data
  }

  async function dismiss(id: string) {
    await riskWarningApi.dismiss(id)
    warnings.value = warnings.value.map(w =>
      w.id === id ? { ...w, dismissed: true } : w
    )
  }

  return { warnings, loading, check, fetchByWork, dismiss }
})
