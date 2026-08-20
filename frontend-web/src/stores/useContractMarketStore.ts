import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/contractMarket'
import type {
  ContractListItem,
  ContractInstance,
  ValidTransitions,
  CreateContractInput,
} from '@/types/contractMarket'

export const useContractMarketStore = defineStore('contractMarket', () => {
  const contracts = ref<ContractListItem[]>([])
  const currentContract = ref<ContractInstance | null>(null)
  const transitions = ref<ValidTransitions | null>(null)
  const loading = ref(false)

  async function loadContracts(params?: Record<string, unknown>) {
    loading.value = true
    try {
      contracts.value = await api.listContracts(params as Record<string, unknown> | undefined)
    } finally {
      loading.value = false
    }
  }

  async function loadContract(id: string) {
    loading.value = true
    try {
      currentContract.value = await api.getContract(id)
    } finally {
      loading.value = false
    }
  }

  async function loadTransitions() {
    transitions.value = await api.getValidTransitions()
  }

  async function createContract(body: CreateContractInput) {
    return api.createContract(body)
  }

  async function publishContract(id: string) {
    const result = await api.publishContract(id)
    await loadContracts()
    return result
  }

  async function transition(
    id: string,
    action: string,
    extra?: Record<string, unknown>,
  ) {
    const fnMap: Record<string, () => Promise<unknown>> = {
      publish: () => api.publishContract(id),
      activate: () => api.activateContract(id),
      subscribe: () => api.subscribeContract(id, (extra?.subscriber_id as string) ?? ''),
      confirmSubscribe: () => api.confirmSubscribe(id),
      escrow: () => api.initiateEscrow(id, (extra?.provider as string) ?? 'stripe'),
      confirmEscrow: () => api.confirmEscrow(id, (extra?.transaction_id as string) ?? ''),
      insurance: () => api.activateInsurance(id, extra as Record<string, unknown> | undefined),
      execute: () => api.startExecution(id),
      complete: () => api.completeContract(id),
      dispute: () => api.disputeContract(id, (extra?.reason as string) ?? ''),
      resolve: () => api.resolveDispute(id, (extra?.resolution as string) ?? ''),
      refund: () => api.refundContract(id, (extra?.reason as string) ?? ''),
      escrowRefund: () => api.escrowRefund(id, (extra?.reason as string) ?? ''),
      release: () => api.releaseEscrow(id),
      cancel: () => api.cancelContract(id, (extra?.reason as string) ?? ''),
    }

    const fn = fnMap[action]
    if (!fn) throw new Error(`Unknown transition: ${action}`)

    const result = await fn()
    await loadContract(id)
    return result
  }

  return {
    contracts,
    currentContract,
    transitions,
    loading,
    loadContracts,
    loadContract,
    loadTransitions,
    createContract,
    publishContract,
    transition,
  }
})
