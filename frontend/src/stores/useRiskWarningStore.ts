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
    } catch (e) {
      console.error('check failed:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchByWork(workId: string) {
    try {
      const res = await riskWarningApi.getByWork(workId)
      warnings.value = res.data.data
    } catch (e) {
      console.error(`fetchByWork(${workId}) failed:`, e)
    }
  }

  async function fetchAll(params?: { dismissed?: boolean; severity?: string }) {
    loading.value = true
    try {
      const res = await riskWarningApi.getAll(params)
      warnings.value = res.data.data
    } catch (e) {
      console.error('fetchAll failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function dismiss(id: string) {
    try {
      await riskWarningApi.dismiss(id)
      warnings.value = warnings.value.map(w =>
        w.id === id ? { ...w, dismissed: true } : w
      )
    } catch (e) {
      console.error(`dismiss(${id}) failed:`, e)
      throw e
    }
  }

  return { warnings, loading, check, fetchAll, fetchByWork, dismiss }
})
