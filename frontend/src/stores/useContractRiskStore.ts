import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reviewContract, getHistory, checkTransaction } from '@/api/contractRisk'
import type { ContractReviewResult, TransactionCheckResult } from '@/types/contractRisk'

export const useContractRiskStore = defineStore('contractRisk', () => {
  const loading = ref(false)
  const result = ref<ContractReviewResult | null>(null)
  const history = ref<any[]>([])

  async function review(data: Parameters<typeof reviewContract>[0]) {
    loading.value = true
    try {
      result.value = await reviewContract(data)
      return result.value
    } finally {
      loading.value = false
    }
  }

  async function fetchHistory(userId: string, limit = 20, page = 1) {
    const res = await getHistory(userId, limit, page)
    history.value = res.data?.reviews ?? []
  }

  async function transactionCheck(data: Parameters<typeof checkTransaction>[0]) {
    return checkTransaction(data)
  }

  function clearResult() {
    result.value = null
  }

  return { loading, result, history, review, fetchHistory, transactionCheck, clearResult }
})
