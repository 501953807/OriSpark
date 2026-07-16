import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RiskWarning, RiskCheckRequest, TaxDeadline, BurnoutRisk } from '@/types/risk_warning'
import { riskWarningApi } from '@/api/risk_warning'
import { listTaxDeadlines, addTaxDeadline, completeTaxDeadline as apiCompleteTaxDeadline, getBurnoutRisk } from '@/api/riskWarning'

export const useRiskWarningStore = defineStore('riskWarning', () => {
  const warnings = ref<RiskWarning[]>([])
  const loading = ref(false)
  const taxDeadlines = ref<TaxDeadline[]>([])
  const burnoutRisk = ref<BurnoutRisk | null>(null)

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

  async function loadTaxDeadlines() {
    const res = await listTaxDeadlines()
    taxDeadlines.value = res
  }

  async function addDeadline(data: { tax_type: string; due_date: string; amount_yuan?: number }) {
    await addTaxDeadline(data)
    await loadTaxDeadlines()
  }

  async function markComplete(id: string) {
    await apiCompleteTaxDeadline(id)
    await loadTaxDeadlines()
  }

  async function loadBurnoutRisk() {
    const res = await getBurnoutRisk()
    burnoutRisk.value = res
  }

  return {
    warnings,
    loading,
    taxDeadlines,
    burnoutRisk,
    check,
    fetchAll,
    fetchByWork,
    dismiss,
    loadTaxDeadlines,
    addDeadline,
    markComplete,
    loadBurnoutRisk,
  }
})
