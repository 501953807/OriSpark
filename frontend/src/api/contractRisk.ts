import { request } from '@/api/client'
import type { ContractReviewRequest, ContractReviewResult, TransactionCheckResult } from '@/types/contractRisk'

export function reviewContract(data: ContractReviewRequest): Promise<ContractReviewResult> {
  return request.post('/contract-risk/review', data).then(res => res.data)
}

export function getHistory(userId: string, limit = 20, page = 1) {
  return request.get(`/contract-risk/history/${userId}?limit=${limit}&page=${page}`)
}

export function checkTransaction(data: {
  listing_id?: string
  contract_template?: string
  custom_terms?: string[]
}): Promise<TransactionCheckResult> {
  return request.post('/contract-risk/transaction-check', data).then(res => res.data)
}
