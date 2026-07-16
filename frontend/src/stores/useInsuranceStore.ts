import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/insurance'
import type {
  InsuranceProduct,
  InsuranceEstimateResponse,
  InsurancePolicy,
  InsuranceClaim,
  InsuranceProvider,
} from '@/types/insurance'

export const useInsuranceStore = defineStore('insurance', () => {
  const products = ref<InsuranceProduct[]>([])
  const policies = ref<InsurancePolicy[]>([])
  const claims = ref<InsuranceClaim[]>([])
  const providers = ref<InsuranceProvider[]>([])
  const estimate = ref<InsuranceEstimateResponse | null>(null)
  const loading = ref(false)

  async function loadProducts(category?: string, tier?: string) {
    loading.value = true
    try {
      products.value = await api.listProducts(category, tier)
    } finally {
      loading.value = false
    }
  }

  async function loadEstimate(data: Parameters<typeof api.estimatePremium>[0]) {
    estimate.value = await api.estimatePremium(data)
    return estimate.value
  }

  async function loadPolicies() {
    policies.value = await api.listPolicies()
  }

  async function submitClaimData(payload: Parameters<typeof api.submitClaim>[0]) {
    return api.submitClaim(payload)
  }

  async function loadProviders() {
    providers.value = await api.listProviders()
  }

  return {
    loading,
    products,
    policies,
    claims,
    providers,
    estimate,
    loadProducts,
    loadEstimate,
    loadPolicies,
    submitClaimData,
    loadProviders,
  }
})
