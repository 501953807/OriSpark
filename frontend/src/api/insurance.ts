import { request } from '@/api/client'
import type {
  InsuranceProduct,
  InsuranceEstimateRequest,
  InsuranceEstimateResponse,
  InsurancePolicy,
  InsuranceClaim,
  InsuranceProvider,
} from '@/types/insurance'

export function listProducts(category?: string, tier?: string) {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  if (tier) params.set('tier', tier)
  return request.get(`/insurance/products?${params}`).then(res => res.data as InsuranceProduct[])
}

export function getProduct(id: string) {
  return request.get(`/insurance/products/${id}`).then(res => res.data as InsuranceProduct)
}

export function estimatePremium(data: InsuranceEstimateRequest) {
  return request.post('/insurance/estimate', data).then(res => res.data as InsuranceEstimateResponse)
}

export function purchasePolicy(productId: string, payload: { start_date: string; duration_months: number }) {
  return request.post(`/insurance/policies/${productId}/purchase`, payload).then(res => res.data)
}

export function listPolicies() {
  return request.get('/insurance/policies').then(res => res.data as InsurancePolicy[])
}

export function submitClaim(payload: { policy_id: string; claim_type: string; description?: string; evidence_urls?: string[]; claimed_amount_yuan?: number }) {
  return request.post('/insurance/claims', payload).then(res => res.data as InsuranceClaim)
}

export function getClaimStatus(claimId: string) {
  return request.get(`/insurance/claims/${claimId}`).then(res => res.data as InsuranceClaim)
}

export function listProviders() {
  return request.get('/insurance/providers').then(res => res.data as InsuranceProvider[])
}
